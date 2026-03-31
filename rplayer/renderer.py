"""Skia-based offscreen renderer for parsed RcDocument objects.

Renders a subset of RemoteCompose operations to a Skia surface, producing
PNG output for validation. Uses skia-python, which wraps the same Skia
library that Android uses internally.

Currently supported:
- Layout containers: root, box, column, row, canvas (simplified positioning)
- Draw operations: rect, circle, line, oval, round_rect, arc, sector, path
- Paint state: color, style, stroke width, cap, join, anti-alias, alpha, gradients
- Modifiers: background, padding, width, height, border, clip
- Text: layout_text, core_text (basic rendering via Skia's drawString)
- Transforms: save, restore, translate, scale, rotate, skew
- Clip: rect, path
- Expression evaluation via RuntimeState (animated/computed values)

Not yet supported:
- Touch/interactivity
- Full layout constraint solving (uses simplified stacking)
- Bitmap font text
- Loop/conditional operations
"""

import math
import skia


# Path command constants (from Rc.PathCommand)
PATH_MOVE = 10
PATH_LINE = 11
PATH_QUADRATIC = 12
PATH_CONIC = 13
PATH_CUBIC = 14
PATH_CLOSE = 15
PATH_DONE = 16
PATH_RESET = 17


class RcRenderer:
    """Renders an RcDocument to a Skia surface.

    Usage:
        renderer = RcRenderer(doc)
        image = renderer.render()      # returns skia.Image
        renderer.save_png('out.png')   # saves to file

    With runtime (for animated rendering):
        from rplayer.runtime import RuntimeState
        rt = RuntimeState(doc)
        renderer = RcRenderer(doc, runtime=rt)
        rt.step(0.5)                   # advance to t=0.5s
        image = renderer.render()      # renders with evaluated expressions
    """

    def __init__(self, doc, scale: float = 1.0, runtime=None):
        self.doc = doc
        self.scale = scale
        self.runtime = runtime
        self.width = max(1, int(doc.width * scale))
        self.height = max(1, int(doc.height * scale))

    def render(self) -> skia.Image:
        """Render the document and return a Skia Image."""
        surface = skia.Surface(self.width, self.height)
        canvas = surface.getCanvas()
        canvas.clear(skia.ColorWHITE)

        if self.scale != 1.0:
            canvas.scale(self.scale, self.scale)

        paint = skia.Paint(AntiAlias=True)
        self._reset_paint(paint)

        ctx = _RenderContext(canvas, paint, self.doc, runtime=self.runtime)
        ctx.execute(self.doc.operations)

        return surface.makeImageSnapshot()

    def save_png(self, path: str) -> int:
        """Render and save to a PNG file. Returns file size in bytes."""
        image = self.render()
        image.save(path, skia.kPNG)
        import os
        return os.path.getsize(path)

    def _reset_paint(self, paint):
        paint.setColor(skia.ColorBLACK)
        paint.setStyle(skia.Paint.kFill_Style)
        paint.setStrokeWidth(0)
        paint.setAntiAlias(True)


class _RenderContext:
    """Internal rendering state machine that walks the operation list."""

    def __init__(self, canvas: skia.Canvas, paint: skia.Paint, doc, runtime=None):
        self.canvas = canvas
        self.paint = paint
        self.doc = doc
        self.runtime = runtime
        self._skia_paths = {}  # path_id -> skia.Path
        self._colors = {}      # id -> ARGB int (from color_constant ops)

    def _rf(self, v: float, default: float = 0.0) -> float:
        """Resolve a float value — if NaN and runtime available, look up variable."""
        if not math.isnan(v):
            return v
        if self.runtime:
            result = self.runtime.resolve_float(v)
            if not math.isnan(result):
                return result
        return default

    def execute(self, ops: list, start: int = 0, end: int = -1):
        """Walk the operation list and render.

        Supports:
        - Conditional blocks: skip to matching 'end' when condition is false
        - Loop blocks: repeat body with incrementing loop variable

        Container 'end' markers are ignored (no layout engine).
        """
        if end < 0:
            end = len(ops)
        i = start
        while i < end:
            o = ops[i]
            op = o.get('op', '')

            if op == 'conditional':
                block_end = self._find_block_end(ops, i + 1)
                if self._eval_condition(o):
                    self.execute(ops, i + 1, block_end)
                i = block_end + 1
                continue

            if op == 'loop_start':
                block_end = self._find_block_end(ops, i + 1)
                self._exec_loop(o, ops, i + 1, block_end)
                i = block_end + 1
                continue

            handler = getattr(self, f'_op_{op}', None)
            if handler:
                handler(o)
            i += 1

    def _eval_condition(self, o) -> bool:
        """Evaluate a conditional operation. Returns True if block should execute."""
        cond_type = o.get('cond_type', 0)
        a = self._rf(o.get('a', 0.0))
        b = self._rf(o.get('b', 0.0))
        if cond_type == 0:    # EQUALS
            return a == b
        elif cond_type == 1:  # NOT_EQUAL
            return a != b
        elif cond_type == 2:  # LESS_THAN
            return a < b
        elif cond_type == 3:  # LESS_THAN_OR_EQUAL
            return a <= b
        elif cond_type == 4:  # GREATER_THAN
            return a > b
        elif cond_type == 5:  # GREATER_THAN_OR_EQUAL
            return a >= b
        return True

    def _find_block_end(self, ops: list, start: int) -> int:
        """Find the matching 'end' for a block (conditional, loop, etc.).

        Returns the index of the matching 'end' op.
        Tracks nesting of ALL block-opening ops (containers, loops, etc.)
        to correctly match the right 'end'.
        """
        _BLOCK_OPS = {
            'conditional', 'loop_start',
            'root', 'box', 'column', 'row', 'canvas', 'canvas_content',
            'content', 'layout_text', 'core_text', 'state_layout',
            'collapsible_row', 'collapsible_column', 'fit_box', 'flow',
        }
        depth = 1
        i = start
        while i < len(ops):
            op = ops[i].get('op', '')
            if op in _BLOCK_OPS:
                depth += 1
            elif op == 'end':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return i  # ran off end

    def _exec_loop(self, o, ops: list, body_start: int, body_end: int):
        """Execute a loop block, iterating with the loop variable."""
        index_id = o.get('index_id', 0)
        from_val = self._rf(o.get('from', 0.0))
        step_val = self._rf(o.get('step', 1.0))
        until_val = self._rf(o.get('until', 0.0))

        if step_val == 0 or (step_val > 0 and from_val >= until_val) or \
           (step_val < 0 and from_val <= until_val):
            return

        # Safety: cap iterations to prevent infinite loops
        max_iters = 10000
        count = 0
        val = from_val
        while count < max_iters:
            if step_val > 0 and val >= until_val:
                break
            if step_val < 0 and val <= until_val:
                break
            # Set loop variable
            if self.runtime:
                self.runtime.floats[index_id] = val
            self.execute(ops, body_start, body_end)
            val += step_val
            count += 1

    # -- Paint state --

    def _op_paint(self, o):
        if 'color_id' in o:
            # Dynamic color — look up from color store or runtime floats
            cid = o['color_id']
            if cid in self._colors:
                argb = self._colors[cid]
            elif self.runtime:
                argb = int(self.runtime.floats.get(cid, 0xFF000000))
            else:
                argb = 0xFF000000
            self.paint.setColor(_argb_to_skia(argb))
        elif 'color' in o:
            self.paint.setColor(_argb_to_skia(o['color']))
        if 'style' in o:
            style_map = {0: skia.Paint.kFill_Style,
                         1: skia.Paint.kStroke_Style,
                         2: skia.Paint.kStrokeAndFill_Style}
            self.paint.setStyle(style_map.get(o['style'], skia.Paint.kFill_Style))
        if 'stroke_width' in o:
            self.paint.setStrokeWidth(self._rf(o['stroke_width']))
        if 'stroke_cap' in o:
            cap_map = {0: skia.Paint.kButt_Cap,
                       1: skia.Paint.kRound_Cap,
                       2: skia.Paint.kSquare_Cap}
            self.paint.setStrokeCap(cap_map.get(o['stroke_cap'], skia.Paint.kButt_Cap))
        if 'stroke_join' in o:
            join_map = {0: skia.Paint.kMiter_Join,
                        1: skia.Paint.kRound_Join,
                        2: skia.Paint.kBevel_Join}
            self.paint.setStrokeJoin(join_map.get(o['stroke_join'], skia.Paint.kMiter_Join))
        if 'anti_alias' in o:
            self.paint.setAntiAlias(o['anti_alias'])
        if 'alpha' in o:
            self.paint.setAlphaf(self._rf(o['alpha'], 1.0))
        if 'stroke_miter' in o:
            self.paint.setStrokeMiter(o['stroke_miter'])
        if 'text_size' in o:
            self._current_text_size = o['text_size']
        if 'typeface_style' in o:
            self._current_typeface_weight = o['typeface_style']
        if 'font_style' in o:
            self._current_font_style = o['font_style']
        if 'blend_mode' in o:
            bm = _map_blend_mode(o['blend_mode'])
            if bm is not None:
                self.paint.setBlendMode(bm)
        if 'gradient' in o:
            grad = o['gradient']
            # Resolve color IDs in gradient: id_mask bitmask indicates which
            # entries in 'colors' are IDs (to look up in _colors) vs raw ARGB.
            id_mask = grad.get('id_mask', 0)
            if id_mask:
                resolved_colors = []
                for idx, c in enumerate(grad.get('colors', [])):
                    if id_mask & (1 << idx):
                        # This is a color ID — resolve it
                        argb = self._colors.get(c, 0xFF000000)
                        resolved_colors.append(argb)
                    else:
                        resolved_colors.append(c)
                grad = dict(grad)
                grad['colors'] = resolved_colors
            shader = _make_gradient_shader(grad)
            if shader:
                self.paint.setShader(shader)
        if 'shader' in o and o['shader'] == 0:
            # Clear shader — create new Paint preserving other state
            old = self.paint
            self.paint = skia.Paint()
            self.paint.setColor(old.getColor())
            self.paint.setStyle(old.getStyle())
            self.paint.setStrokeWidth(old.getStrokeWidth())
            self.paint.setAntiAlias(old.isAntiAlias())
            self.paint.setStrokeCap(old.getStrokeCap())
            self.paint.setStrokeJoin(old.getStrokeJoin())

    # -- Draw operations --

    def _op_draw_rect(self, o):
        self.canvas.drawRect(skia.Rect(
            self._rf(o['left']), self._rf(o['top']),
            self._rf(o['right']), self._rf(o['bottom'])), self.paint)

    def _op_draw_circle(self, o):
        self.canvas.drawCircle(
            self._rf(o['cx']), self._rf(o['cy']),
            self._rf(o['r'], 1.0), self.paint)

    def _op_draw_line(self, o):
        self.canvas.drawLine(
            self._rf(o['x1']), self._rf(o['y1']),
            self._rf(o['x2']), self._rf(o['y2']), self.paint)

    def _op_draw_round_rect(self, o):
        rect = skia.Rect(
            self._rf(o['left']), self._rf(o['top']),
            self._rf(o['right']), self._rf(o['bottom']))
        rrect = skia.RRect.MakeRectXY(rect,
            self._rf(o['rx'], 1.0), self._rf(o['ry'], 1.0))
        self.canvas.drawRRect(rrect, self.paint)

    def _op_draw_oval(self, o):
        rect = skia.Rect(
            self._rf(o['left']), self._rf(o['top']),
            self._rf(o['right']), self._rf(o['bottom']))
        self.canvas.drawOval(rect, self.paint)

    def _op_draw_arc(self, o):
        rect = skia.Rect(
            self._rf(o['left']), self._rf(o['top']),
            self._rf(o['right']), self._rf(o['bottom']))
        self.canvas.drawArc(rect,
            self._rf(o['start_angle']), self._rf(o['sweep_angle']),
            False, self.paint)

    def _op_draw_sector(self, o):
        rect = skia.Rect(
            self._rf(o['left']), self._rf(o['top']),
            self._rf(o['right']), self._rf(o['bottom']))
        self.canvas.drawArc(rect,
            self._rf(o['start_angle']), self._rf(o['sweep_angle']),
            True, self.paint)

    def _op_draw_path(self, o):
        path = self._get_path(o['path_id'])
        if path:
            self.canvas.drawPath(path, self.paint)

    def _make_font(self):
        """Create a Skia Font with current text size and typeface weight/style."""
        text_size = getattr(self, '_current_text_size', 14.0)
        weight = getattr(self, '_current_typeface_weight', 400)
        style = getattr(self, '_current_font_style', 0)
        slant = skia.FontStyle.kItalic_Slant if style == 1 else skia.FontStyle.kUpright_Slant
        width = skia.FontStyle.kNormal_Width
        fs = skia.FontStyle(weight, width, slant)
        typeface = skia.Typeface.MakeFromName(None, fs)
        font = skia.Font(typeface, text_size)
        return font

    def _op_draw_text_run(self, o):
        text_id = o['text_id']
        text = self._resolve_text(text_id)
        font = self._make_font()
        self.canvas.drawString(text, self._rf(o['x']), self._rf(o['y']),
                               font, self.paint)

    def _op_draw_text_anchor(self, o):
        text_id = o['text_id']
        text = self._resolve_text(text_id)
        if not text:
            return
        font = self._make_font()

        x_pos = self._rf(o['x'])
        y_pos = self._rf(o['y'])
        pan_x = self._rf(o['pan_x'])
        pan_y = self._rf(o['pan_y'])

        # Get text bounds (matching Java Paint.getTextBounds)
        blob = skia.TextBlob.MakeFromString(text, font)
        if not blob:
            return
        bounds = blob.bounds()

        text_width = bounds.right() - bounds.left()
        text_height = bounds.bottom() - bounds.top()

        # Match Java DrawTextAnchored.getHorizontalOffset (boxWidth=0)
        h_offset = -text_width * (1 + pan_x) / 2.0 - bounds.left()

        # Match Java DrawTextAnchored.getVerticalOffset (boxHeight=0)
        flags = o.get('flags', 0)
        baseline = (flags & 8) != 0  # BASELINE_RELATIVE = 8
        if baseline:
            v_offset = -text_height * (1 - pan_y) / 2.0 + text_height / 2.0
        else:
            v_offset = -text_height * (1 - pan_y) / 2.0 - bounds.top()

        self.canvas.drawString(text, x_pos + h_offset, y_pos + v_offset,
                               font, self.paint)

    def _op_draw_text_on_circle(self, o):
        text = self.doc.texts.get(o['text_id'], '')
        if not text:
            return
        font = self._make_font()
        cx, cy, radius = o['cx'], o['cy'], o['radius']
        start = math.radians(o['start_angle'])
        # Approximate: space characters evenly around the arc
        char_angle = 0.15  # rough angle per character
        for i, ch in enumerate(text):
            angle = start + i * char_angle
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            self.canvas.save()
            self.canvas.translate(x, y)
            self.canvas.rotate(math.degrees(angle) + 90)
            self.canvas.drawString(ch, 0, 0, font, self.paint)
            self.canvas.restore()

    # -- Layout (simplified — just tracks modifier state) --

    def _op_root(self, o):
        pass

    def _op_box(self, o):
        pass

    def _op_row(self, o):
        pass

    def _op_column(self, o):
        pass

    def _op_canvas(self, o):
        pass

    def _op_canvas_content(self, o):
        pass

    def _op_canvas_operations(self, o):
        pass

    def _op_content(self, o):
        pass

    def _op_fit_box(self, o):
        pass

    def _op_flow(self, o):
        pass

    def _op_state_layout(self, o):
        pass

    def _op_image(self, o):
        pass

    def _op_end(self, o):
        pass

    def _op_component_start(self, o):
        pass

    # -- Text components --

    def _resolve_text(self, text_id: int) -> str:
        """Resolve text by ID, checking runtime then doc."""
        if self.runtime:
            t = self.runtime.texts.get(text_id, '')
            if t:
                return t
        return self.doc.texts.get(text_id, '')

    def _op_layout_text(self, o):
        text = self._resolve_text(o['text_id'])
        if not text:
            return
        color = o.get('color', 0xFF000000)
        font_size = self._rf(o.get('font_size', 14.0), 14.0)

        text_paint = skia.Paint(AntiAlias=True)
        text_paint.setColor(_argb_to_skia(color))
        weight = int(self._rf(o.get('font_weight', 400.0), 400.0))
        style = o.get('font_style', 0)
        slant = skia.FontStyle.kItalic_Slant if style == 1 else skia.FontStyle.kUpright_Slant
        fs = skia.FontStyle(weight, skia.FontStyle.kNormal_Width, slant)
        typeface = skia.Typeface.MakeFromName(None, fs)
        font = skia.Font(typeface, font_size)

        self.canvas.save()
        self.canvas.drawString(text, 10, font_size + 5, font, text_paint)
        self.canvas.restore()

    def _op_core_text(self, o):
        text = self._resolve_text(o['text_id'])
        if not text:
            return
        color = o.get('color', 0xFF000000)
        font_size = self._rf(o.get('font_size', 36.0), 36.0)

        text_paint = skia.Paint(AntiAlias=True)
        text_paint.setColor(_argb_to_skia(color))
        weight = int(self._rf(o.get('font_weight', 400.0), 400.0))
        style = o.get('font_style', 0)
        slant = skia.FontStyle.kItalic_Slant if style == 1 else skia.FontStyle.kUpright_Slant
        fs = skia.FontStyle(weight, skia.FontStyle.kNormal_Width, slant)
        typeface = skia.Typeface.MakeFromName(None, fs)
        font = skia.Font(typeface, font_size)

        self.canvas.save()
        self.canvas.drawString(text, 10, font_size + 5, font, text_paint)
        self.canvas.restore()

    # -- Modifiers (affect subsequent container/component) --

    def _op_mod_background(self, o):
        flags = o.get('flags', 0)
        if flags & 2 and o.get('color_id', 0):
            # Dynamic color — resolve from color store
            cid = o['color_id']
            color = self._colors.get(cid, 0)
            if color == 0 and self.runtime:
                color = int(self.runtime.floats.get(cid, 0))
        else:
            color = o.get('color', 0)
        if (color >> 24) & 0xFF > 0:
            bg_paint = skia.Paint(AntiAlias=True)
            bg_paint.setColor(_argb_to_skia(color))
            shape = o.get('shape', 0)
            rect = skia.Rect(0, 0, self.doc.width, self.doc.height)
            cr = o.get('corner_radius', 0.0)
            if shape == 1 and cr > 0:
                bg_paint.setStyle(skia.Paint.kFill_Style)
                rrect = skia.RRect.MakeRectXY(rect, cr, cr)
                self.canvas.drawRRect(rrect, bg_paint)
            else:
                self.canvas.drawRect(rect, bg_paint)

    def _op_mod_padding(self, o):
        pass  # simplified: no layout constraint solving yet

    def _op_mod_width(self, o):
        pass

    def _op_mod_height(self, o):
        pass

    def _op_mod_width_in(self, o):
        pass

    def _op_mod_height_in(self, o):
        pass

    def _op_mod_border(self, o):
        color = o.get('color', 0)
        bw = o.get('border_width', 1.0)
        if (color >> 24) & 0xFF > 0:
            border_paint = skia.Paint(AntiAlias=True)
            border_paint.setColor(_argb_to_skia(color))
            border_paint.setStyle(skia.Paint.kStroke_Style)
            border_paint.setStrokeWidth(bw)
            cr = o.get('corner_radius', 0.0)
            rect = skia.Rect(0, 0, self.doc.width, self.doc.height)
            if cr > 0:
                rrect = skia.RRect.MakeRectXY(rect, cr, cr)
                self.canvas.drawRRect(rrect, border_paint)
            else:
                self.canvas.drawRect(rect, border_paint)

    def _op_mod_clip_rect(self, o):
        pass

    def _op_mod_rounded_clip(self, o):
        pass

    def _op_mod_offset(self, o):
        pass

    def _op_mod_visibility(self, o):
        pass

    def _op_mod_zindex(self, o):
        pass

    def _op_mod_scroll(self, o):
        pass

    def _op_mod_marquee(self, o):
        pass

    def _op_mod_graphics_layer(self, o):
        pass

    def _op_mod_ripple(self, o):
        pass

    def _op_mod_align_by(self, o):
        pass

    def _op_mod_collapsible_priority(self, o):
        pass

    def _op_mod_click(self, o):
        pass

    def _op_mod_touch_down(self, o):
        pass

    def _op_mod_touch_up(self, o):
        pass

    def _op_mod_touch_cancel(self, o):
        pass

    def _op_mod_draw_content(self, o):
        pass

    # -- Transforms --

    def _op_matrix_save(self, o):
        self.canvas.save()

    def _op_matrix_restore(self, o):
        self.canvas.restore()

    def _op_matrix_translate(self, o):
        dx = self._rf(o['dx'])
        dy = self._rf(o['dy'])
        self.canvas.translate(dx, dy)

    def _op_matrix_scale(self, o):
        sx = self._rf(o['sx'], 1.0)
        sy = self._rf(o['sy'], 1.0)
        raw_cx = o.get('cx', float('nan'))
        raw_cy = o.get('cy', float('nan'))
        cx = self._rf(raw_cx) if math.isnan(raw_cx) else raw_cx
        cy = self._rf(raw_cy) if math.isnan(raw_cy) else raw_cy
        has_center = not math.isnan(cx) and not math.isnan(cy)
        if has_center:
            self.canvas.translate(cx, cy)
            self.canvas.scale(sx, sy)
            self.canvas.translate(-cx, -cy)
        else:
            self.canvas.scale(sx, sy)

    def _op_matrix_rotate(self, o):
        angle = self._rf(o['angle'])
        cx = self._rf(o['cx'])
        cy = self._rf(o['cy'])
        if cx != 0.0 or cy != 0.0:
            self.canvas.rotate(angle, cx, cy)
        else:
            self.canvas.rotate(angle)

    def _op_matrix_skew(self, o):
        sx = self._rf(o['sx'])
        sy = self._rf(o['sy'])
        self.canvas.skew(sx, sy)

    # -- Clip --

    def _op_clip_rect(self, o):
        self.canvas.clipRect(skia.Rect(o['left'], o['top'],
                                        o['right'], o['bottom']))

    def _op_clip_path(self, o):
        path = self._get_path(o['path_id'])
        if path:
            self.canvas.clipPath(path)

    # -- Data / no-op operations (already parsed into doc) --

    def _op_data_path(self, o):
        self._build_path(o['id'], o['data'])

    def _op_data_int(self, o):
        pass

    def _op_data_long(self, o):
        pass

    def _op_data_bool(self, o):
        pass

    def _op_data_bitmap(self, o):
        pass

    def _op_data_shader(self, o):
        pass

    def _op_data_font(self, o):
        pass

    def _op_data_bitmap_font(self, o):
        pass

    def _op_animated_float(self, o):
        """Re-evaluate a float expression with current runtime state.

        Critical for expressions inside loops/conditionals — the loop variable
        changes each iteration, so dependent expressions must be re-evaluated.
        """
        if not self.runtime:
            return
        fid = o['id']
        expr = o.get('expression', [])
        if not expr:
            return
        from .expressions import from_nan as _fn, is_math_operator, is_data_variable
        # Resolve variable references in the expression using current floats
        resolved = []
        for v in expr:
            if math.isnan(v):
                if is_math_operator(v) or is_data_variable(v):
                    resolved.append(v)  # keep operators/data refs as-is
                else:
                    var_id = _fn(v)
                    resolved.append(self.runtime.floats.get(var_id, 0.0))
            else:
                resolved.append(v)
        result = self.runtime.evaluator.eval(
            resolved, collections=self.runtime.collections)
        self.runtime.floats[fid] = result

    def _op_integer_expression(self, o):
        pass

    def _op_named_variable(self, o):
        pass

    def _op_color_constant(self, o):
        cid = o.get('id', 0)
        color = o.get('color', 0)
        self._colors[cid] = color

    def _op_color_expression(self, o):
        """Evaluate a color expression.

        mode_packed format: (alpha << 16) | mode
        Modes:
          0 = INTERPOLATE: blend between v1,v2,v3 colors using a float driver
          1 = SET_ARGB: set A,R,G,B channels from float variable values
          2 = MODIFY_ALPHA: adjust alpha of a base color
          3 = SELECT: pick between two colors (v1,v2) based on v3
          4 = HSV: construct color from hue/saturation/value floats
        """
        out_id = o.get('out_id', 0)
        mode_packed = o.get('mode', 0)
        v1 = o.get('v1', 0)
        v2 = o.get('v2', 0)
        v3 = o.get('v3', 0)
        import struct

        actual_mode = mode_packed & 0xFF
        alpha_packed = (mode_packed >> 16) & 0xFFFF

        def _int_as_float(iv):
            """Interpret raw int as IEEE 754 float bits, then resolve NaN refs."""
            fv = struct.unpack('f', struct.pack('I', iv & 0xFFFFFFFF))[0]
            return self._rf(fv, 0.0)

        if actual_mode == 0:
            # Interpolate: v1, v2, v3 are raw ARGB colors
            # Driver float is typically out_id - 1
            t_val = 0.0
            if self.runtime:
                t_val = self.runtime.floats.get(out_id - 1, 0.0)
            colors = [v1, v2, v3]
            t_clamped = max(0.0, min(1.0, t_val))
            n = len(colors) - 1
            if n <= 0:
                result = colors[0]
            else:
                pos = t_clamped * n
                idx = min(int(pos), n - 1)
                frac = pos - idx
                c1 = colors[idx]
                c2 = colors[min(idx + 1, n)]
                a = int(((c1 >> 24) & 0xFF) * (1 - frac) + ((c2 >> 24) & 0xFF) * frac) & 0xFF
                r = int(((c1 >> 16) & 0xFF) * (1 - frac) + ((c2 >> 16) & 0xFF) * frac) & 0xFF
                g = int(((c1 >> 8) & 0xFF) * (1 - frac) + ((c2 >> 8) & 0xFF) * frac) & 0xFF
                b = int((c1 & 0xFF) * (1 - frac) + (c2 & 0xFF) * frac) & 0xFF
                result = (a << 24) | (r << 16) | (g << 8) | b
        elif actual_mode == 3:
            # SELECT: v1, v2 are color IDs, v3 selects which one
            is_second = False
            if isinstance(v3, int) and v3 != 0:
                try:
                    fv3 = struct.unpack('f', struct.pack('I', v3 & 0xFFFFFFFF))[0]
                    is_second = (fv3 > 0.5)
                except:
                    is_second = True
            color_id = v2 if is_second else v1
            result = self._colors.get(color_id, 0xFF000000)
        elif actual_mode == 4:
            # HSV: v1=hue bits, v2=saturation bits, v3=value/brightness bits
            hue = _int_as_float(v1)
            sat = _int_as_float(v2)
            val = _int_as_float(v3)
            alpha = min(255, max(0, alpha_packed)) if alpha_packed else 0xFF

            # HSV→RGB matching Java Utils.hsvToRgb exactly
            # hue is 0.0-1.0 (NOT degrees 0-360)
            h = int(hue * 6) % 6
            f = hue * 6 - int(hue * 6)
            p = int(0.5 + 255 * val * (1 - sat))
            q = int(0.5 + 255 * val * (1 - f * sat))
            t = int(0.5 + 255 * val * (1 - (1 - f) * sat))
            v = int(0.5 + 255 * val)
            p = max(0, min(255, p))
            q = max(0, min(255, q))
            t = max(0, min(255, t))
            v = max(0, min(255, v))
            if h == 0:
                ri, gi, bi = v, t, p
            elif h == 1:
                ri, gi, bi = q, v, p
            elif h == 2:
                ri, gi, bi = p, v, t
            elif h == 3:
                ri, gi, bi = p, q, v
            elif h == 4:
                ri, gi, bi = t, p, v
            else:
                ri, gi, bi = v, p, q
            result = (alpha << 24) | (ri << 16) | (gi << 8) | bi
        else:
            # Modes 1, 2: not fully supported; use v1 as color ID fallback
            result = self._colors.get(v1, v1 if v1 > 0xFFFFFF else 0xFF000000)

        self._colors[out_id] = result
        if self.runtime:
            self.runtime.floats[out_id] = float(result)

    def _op_color_theme(self, o):
        pass

    def _op_text_from_float(self, o):
        out_id = o.get('out_id', 0)
        raw_value = o.get('value', 0.0)
        before = o.get('before', 0)
        after = o.get('after', 0)
        flags = o.get('flags', 0)

        # Resolve the value (may be NaN-encoded variable reference)
        val = self._rf(raw_value, 0.0)

        # Extract padding characters from flags (matches Java TextFromFloat)
        # bit pattern: . F L O O _ S S G G _ P P A A
        pre_bits = flags & 0x0C  # bits 2-3
        post_bits = flags & 0x03  # bits 0-1
        if pre_bits == 0:      # PAD_PRE_SPACE
            pre_char = ' '
        elif pre_bits == 4:    # PAD_PRE_NONE
            pre_char = ''
        elif pre_bits == 12:   # PAD_PRE_ZERO
            pre_char = '0'
        else:
            pre_char = ' '

        if post_bits == 0:     # PAD_AFTER_SPACE
            post_char = ' '
        elif post_bits == 1:   # PAD_AFTER_NONE
            post_char = ''
        elif post_bits == 3:   # PAD_AFTER_ZERO
            post_char = '0'
        else:
            post_char = ' '

        full_format = (flags & 0x800) != 0  # FULL_FORMAT bit
        if full_format:
            text = str(val)
            if self.runtime:
                self.runtime.texts[out_id] = text
            else:
                self.doc.texts[out_id] = text
            return

        # Match Java StringUtils.floatToString logic
        is_neg = val < 0
        abs_val = abs(val)
        int_part = int(abs_val)
        int_str = str(int_part)

        # Pad or truncate integer part
        if len(int_str) < before and pre_char:
            int_str = int_str.rjust(before, pre_char)
        elif len(int_str) > before > 0:
            # Java truncates to last N digits
            int_str = int_str[len(int_str) - before:]

        if after == 0:
            text = ('-' if is_neg else '') + int_str
        else:
            # Fractional part — match Java rounding approach
            frac = abs_val % 1
            for _ in range(after):
                frac *= 10
            frac = round(frac)
            for _ in range(after):
                frac *= 0.1
            frac_str = f'{frac:.{after}f}'
            # Take digits after "0."
            if '.' in frac_str:
                frac_str = frac_str.split('.')[1][:after]
            else:
                frac_str = '0' * after
            # Trim trailing zeros (Java behavior), then post-pad
            trimmed = frac_str.rstrip('0') or ''
            if post_char and len(trimmed) < after:
                trimmed = trimmed + post_char * (after - len(trimmed))
            text = ('-' if is_neg else '') + int_str + '.' + trimmed

        # Store in runtime texts (or doc texts if no runtime)
        if self.runtime:
            self.runtime.texts[out_id] = text
        else:
            self.doc.texts[out_id] = text

    def _op_text_merge(self, o):
        id1 = o.get('id1', 0)
        id2 = o.get('id2', 0)
        out_id = o.get('out_id', 0)
        t1 = self._resolve_text(id1)
        t2 = self._resolve_text(id2)
        text = t1 + t2
        if self.runtime:
            self.runtime.texts[out_id] = text
        else:
            self.doc.texts[out_id] = text

    def _op_text_lookup(self, o):
        text_id = o.get('text_id', 0)
        data_set_id = o.get('data_set_id', 0)
        index_val = o.get('index', 0.0)
        idx = int(self._rf(index_val, 0.0))
        # Look up text from a data set (list of text IDs)
        arr = []
        if self.runtime:
            arr = self.runtime.collections.float_arrays.get(data_set_id, [])
        if 0 <= idx < len(arr):
            src_text_id = int(arr[idx])
            text = self._resolve_text(src_text_id)
        else:
            text = self._resolve_text(data_set_id)
        if self.runtime:
            self.runtime.texts[text_id] = text
        else:
            self.doc.texts[text_id] = text

    def _op_text_lookup_int(self, o):
        text_id = o.get('text_id', 0)
        data_set_id = o.get('data_set_id', 0)
        index_id = o.get('index_id', 0)
        idx = 0
        if self.runtime:
            idx = self.runtime.integers.get(index_id, 0)
        arr = []
        if self.runtime:
            arr = self.runtime.collections.float_arrays.get(data_set_id, [])
        if 0 <= idx < len(arr):
            src_text_id = int(arr[idx])
            text = self._resolve_text(src_text_id)
        else:
            text = self._resolve_text(data_set_id)
        if self.runtime:
            self.runtime.texts[text_id] = text
        else:
            self.doc.texts[text_id] = text

    def _op_text_subtext(self, o):
        out_id = o.get('out_id', 0)
        text_id = o.get('text_id', 0)
        start = int(self._rf(o.get('start', 0.0)))
        length = int(self._rf(o.get('length', -1.0)))
        text = self._resolve_text(text_id)
        if length < 0:
            result = text[start:]
        else:
            result = text[start:start + length]
        if self.runtime:
            self.runtime.texts[out_id] = result
        else:
            self.doc.texts[out_id] = result

    def _op_text_transform(self, o):
        out_id = o.get('out_id', 0)
        text_id = o.get('text_id', 0)
        start = int(o.get('start', 0.0))
        length = int(o.get('length', -1.0))
        operation = o.get('operation', 0)
        text = self._resolve_text(text_id)
        if length < 0:
            target = text[start:]
            prefix = text[:start]
        else:
            target = text[start:start + length]
            prefix = text[:start]
            suffix = text[start + length:]
        # Operations: 0=none, 1=uppercase, 2=lowercase, 3=capitalize, 4=title, 5=reverse
        if operation == 1:
            target = target.upper()
        elif operation == 2:
            target = target.lower()
        elif operation == 3:
            target = target.capitalize()
        elif operation == 4:
            target = target.title()
        elif operation == 5:
            target = target[::-1]
        if length < 0:
            result = prefix + target
        else:
            result = prefix + target + suffix
        if self.runtime:
            self.runtime.texts[out_id] = result
        else:
            self.doc.texts[out_id] = result

    def _op_text_measure(self, o):
        out_id = o.get('out_id', 0)
        text_id = o.get('text_id', 0)
        text = self._resolve_text(text_id)
        font = self._make_font()
        width = font.measureText(text)
        if self.runtime:
            self.runtime.floats[out_id] = width
        else:
            self.doc.floats[out_id] = width

    def _op_text_length(self, o):
        out_id = o.get('out_id', 0)
        text_id = o.get('text_id', 0)
        text = self._resolve_text(text_id)
        if self.runtime:
            self.runtime.floats[out_id] = float(len(text))
        else:
            self.doc.floats[out_id] = float(len(text))

    def _op_text_style(self, o):
        pass

    def _op_attr_text(self, o):
        pass

    def _op_attr_image(self, o):
        pass

    def _op_attr_time(self, o):
        pass

    def _op_attr_color(self, o):
        pass

    def _op_id_map(self, o):
        pass

    def _op_id_list(self, o):
        pass

    def _op_float_list(self, o):
        pass

    def _op_dynamic_float_list(self, o):
        pass

    def _op_update_dynamic_float_list(self, o):
        pass

    def _op_id_lookup(self, o):
        pass

    def _op_data_map_lookup(self, o):
        pass

    def _op_component_value(self, o):
        pass

    def _op_animation_spec(self, o):
        pass

    def _op_touch_expression(self, o):
        pass

    def _op_path_tween(self, o):
        pass

    def _op_path_create(self, o):
        """Create a new runtime path and moveTo the initial point."""
        pid = o['id']
        x = self._rf(o.get('x', 0.0))
        y = self._rf(o.get('y', 0.0))
        path = skia.Path()
        path.moveTo(x, y)
        self._skia_paths[pid] = path

    def _op_path_add(self, o):
        """Append path commands to an existing runtime path.

        Same wire format as _build_path (2-slot padding after LINE/QUAD/etc).
        """
        pid = o['path_id']
        path = self._skia_paths.get(pid)
        if path is None:
            return
        data = o.get('values', [])
        if not data:
            return
        from .expressions import from_nan as _from_nan
        i = 0

        def _val(idx):
            v = data[idx]
            if math.isnan(v):
                return self._rf(v, 0.0)
            return v

        while i < len(data):
            raw = data[i]
            if math.isnan(raw):
                cmd = _from_nan(raw)
            elif math.isinf(raw):
                break
            else:
                cmd = int(raw)
            i += 1
            if cmd == PATH_MOVE:
                if i + 1 < len(data):
                    path.moveTo(_val(i), _val(i + 1))
                    i += 2
            elif cmd == PATH_LINE:
                i += 2  # skip padding
                if i + 1 < len(data):
                    path.lineTo(_val(i), _val(i + 1))
                    i += 2
            elif cmd == PATH_QUADRATIC:
                i += 2
                if i + 3 < len(data):
                    path.quadTo(_val(i), _val(i + 1), _val(i + 2), _val(i + 3))
                    i += 4
            elif cmd == PATH_CONIC:
                i += 2
                if i + 4 < len(data):
                    path.conicTo(_val(i), _val(i + 1), _val(i + 2), _val(i + 3),
                                _val(i + 4))
                    i += 5
            elif cmd == PATH_CUBIC:
                i += 2
                if i + 5 < len(data):
                    path.cubicTo(_val(i), _val(i + 1), _val(i + 2), _val(i + 3),
                                _val(i + 4), _val(i + 5))
                    i += 6
            elif cmd == PATH_CLOSE:
                path.close()
            elif cmd == PATH_DONE:
                break
            elif cmd == PATH_RESET:
                path.reset()
            else:
                # Unknown command — might be a raw coordinate for lineTo
                # (some paths use implicit lineTo for sequential coords)
                if i < len(data):
                    path.lineTo(raw if not math.isnan(raw) else self._rf(raw, 0.0),
                                _val(i))
                    i += 1

    def _op_path_combine(self, o):
        pass

    def _op_path_expression(self, o):
        pass

    def _op_theme(self, o):
        pass

    def _op_root_content_behavior(self, o):
        pass

    def _op_root_content_description(self, o):
        pass

    def _op_click_area(self, o):
        pass

    def _op_debug(self, o):
        pass

    def _op_haptic(self, o):
        pass

    def _op_rem(self, o):
        pass

    def _op_skip(self, o):
        pass

    # loop_start is handled directly in execute() — no handler needed

    def _op_host_action(self, o):
        pass

    def _op_host_named_action(self, o):
        pass

    def _op_host_metadata_action(self, o):
        pass

    def _op_float_change(self, o):
        pass

    def _op_int_change(self, o):
        pass

    def _op_string_change(self, o):
        pass

    def _op_float_expr_change(self, o):
        pass

    def _op_int_expr_change(self, o):
        pass

    def _op_run_action(self, o):
        pass

    def _op_draw_content(self, o):
        pass

    def _op_draw_bitmap(self, o):
        pass

    def _op_draw_bitmap_scaled(self, o):
        pass

    def _op_draw_to_bitmap(self, o):
        pass

    def _op_draw_bitmap_int(self, o):
        pass

    def _op_draw_text_on_path(self, o):
        pass

    def _op_draw_tween_path(self, o):
        pass

    def _op_draw_bitmap_font_text_run(self, o):
        pass

    def _op_draw_bitmap_font_text_run_on_path(self, o):
        pass

    def _op_draw_bitmap_text_anchored(self, o):
        pass

    def _op_bitmap_text_measure(self, o):
        pass

    def _op_matrix_set(self, o):
        pass

    def _op_matrix_from_path(self, o):
        pass

    def _op_matrix_constant(self, o):
        pass

    def _op_matrix_expression(self, o):
        pass

    def _op_matrix_vector_math(self, o):
        pass

    def _op_collapsible_row(self, o):
        pass

    def _op_collapsible_column(self, o):
        pass

    def _op_layout_compute(self, o):
        pass

    def _op_accessibility(self, o):
        pass

    def _op_impulse_start(self, o):
        pass

    def _op_impulse_process(self, o):
        pass

    def _op_function_define(self, o):
        pass

    def _op_function_call(self, o):
        pass

    def _op_update(self, o):
        pass

    def _op_wake_in(self, o):
        pass

    def _op_load_bitmap(self, o):
        pass

    def _op_particle_compare(self, o):
        pass

    # -- Path building --

    def _build_path(self, path_id: int, data: list):
        """Build a skia.Path from a float data array (path commands).

        Wire format (from RemotePath): commands are NaN-encoded. After the
        command, LINE/QUADRATIC/CONIC/CUBIC have 2-slot zero padding before
        their coordinate data. MOVE has NO padding. CLOSE/DONE/RESET have
        no following data.

        Format per command:
          MOVE:      [CMD, x, y]                          (3 floats)
          LINE:      [CMD, pad, pad, x, y]                (5 floats)
          QUADRATIC: [CMD, pad, pad, x1, y1, x2, y2]     (7 floats)
          CONIC:     [CMD, pad, pad, x1, y1, x2, y2, w]  (8 floats)
          CUBIC:     [CMD, pad, pad, x1..y3]              (9 floats)
          CLOSE:     [CMD]                                (1 float)
          DONE:      [CMD]                                (1 float)
        """
        from .expressions import from_nan as _from_nan
        path = skia.Path()
        i = 0

        def _val(idx):
            v = data[idx]
            if math.isnan(v):
                return self._rf(v, 0.0)
            return v

        while i < len(data):
            raw = data[i]
            if math.isnan(raw):
                cmd = _from_nan(raw)
            elif math.isinf(raw):
                break
            else:
                cmd = int(raw)
            i += 1
            if cmd == PATH_MOVE:
                if i + 1 < len(data):
                    path.moveTo(_val(i), _val(i + 1))
                    i += 2
            elif cmd == PATH_LINE:
                i += 2  # skip 2-slot padding
                if i + 1 < len(data):
                    path.lineTo(_val(i), _val(i + 1))
                    i += 2
            elif cmd == PATH_QUADRATIC:
                i += 2  # skip padding
                if i + 3 < len(data):
                    path.quadTo(_val(i), _val(i + 1), _val(i + 2), _val(i + 3))
                    i += 4
            elif cmd == PATH_CONIC:
                i += 2  # skip padding
                if i + 4 < len(data):
                    path.conicTo(_val(i), _val(i + 1), _val(i + 2), _val(i + 3),
                                _val(i + 4))
                    i += 5
            elif cmd == PATH_CUBIC:
                i += 2  # skip padding
                if i + 5 < len(data):
                    path.cubicTo(_val(i), _val(i + 1), _val(i + 2), _val(i + 3),
                                _val(i + 4), _val(i + 5))
                    i += 6
            elif cmd == PATH_CLOSE:
                path.close()
            elif cmd == PATH_DONE:
                break
            elif cmd == PATH_RESET:
                path.reset()
            else:
                break
        self._skia_paths[path_id] = path

    def _get_path(self, path_id: int):
        """Get a previously built Skia path, building from doc.paths if needed."""
        if path_id not in self._skia_paths:
            if path_id in self.doc.paths:
                self._build_path(path_id, self.doc.paths[path_id])
        return self._skia_paths.get(path_id)


# -- Utility functions --

def _argb_to_skia(argb: int) -> int:
    """Convert ARGB int to Skia color (which is also ARGB)."""
    return argb & 0xFFFFFFFF


def _map_blend_mode(mode: int):
    """Map RemoteCompose blend mode ordinal to Skia blend mode."""
    blend_map = {
        0: skia.BlendMode.kClear,
        1: skia.BlendMode.kSrc,
        2: skia.BlendMode.kDst,
        3: skia.BlendMode.kSrcOver,
        4: skia.BlendMode.kDstOver,
        5: skia.BlendMode.kSrcIn,
        6: skia.BlendMode.kDstIn,
        7: skia.BlendMode.kSrcOut,
        8: skia.BlendMode.kDstOut,
        9: skia.BlendMode.kSrcATop,
        10: skia.BlendMode.kDstATop,
        11: skia.BlendMode.kXor,
        12: skia.BlendMode.kPlus,
        13: skia.BlendMode.kModulate,
        14: skia.BlendMode.kScreen,
        15: skia.BlendMode.kOverlay,
        16: skia.BlendMode.kDarken,
        17: skia.BlendMode.kLighten,
    }
    return blend_map.get(mode)


def _safe_float(v, default=0.0):
    """Return v if it's a finite number, else default (handles NaN expression refs)."""
    import math
    if isinstance(v, (int, float)) and not math.isnan(v) and not math.isinf(v):
        return float(v)
    return default


def _make_gradient_shader(grad: dict):
    """Create a Skia shader from a gradient definition."""
    colors = [_argb_to_skia(c) for c in grad.get('colors', [])]
    if not colors:
        return None

    positions = grad.get('positions', [])
    if not positions:
        positions = None
    else:
        positions = [_safe_float(p, i / max(len(positions) - 1, 1))
                     for i, p in enumerate(positions)]

    gtype = grad.get('type', 0)

    tile_mode_map = {0: skia.TileMode.kClamp,
                     1: skia.TileMode.kMirror,
                     2: skia.TileMode.kRepeat,
                     3: skia.TileMode.kDecal}

    if gtype == 0:  # LINEAR
        tm = tile_mode_map.get(grad.get('tile_mode', 0), skia.TileMode.kClamp)
        pts = [skia.Point(_safe_float(grad.get('start_x')),
                          _safe_float(grad.get('start_y'))),
               skia.Point(_safe_float(grad.get('end_x'), 100.0),
                          _safe_float(grad.get('end_y'), 100.0))]
        return skia.GradientShader.MakeLinear(pts, colors, positions, tm)

    elif gtype == 1:  # RADIAL
        tm = tile_mode_map.get(grad.get('tile_mode', 0), skia.TileMode.kClamp)
        center = skia.Point(_safe_float(grad.get('center_x')),
                            _safe_float(grad.get('center_y')))
        radius = _safe_float(grad.get('radius'), 50.0)
        if radius <= 0:
            radius = 50.0
        return skia.GradientShader.MakeRadial(center, radius,
                                               colors, positions, tm)

    elif gtype == 2:  # SWEEP
        return skia.GradientShader.MakeSweep(
            _safe_float(grad.get('center_x')),
            _safe_float(grad.get('center_y')),
            colors, positions)

    return None
