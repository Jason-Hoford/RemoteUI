"""Flow control demos. Port of FlowControlChecks.java.

Covers: testConditional, flowControlChecks1, flowControlChecks2.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan, id_from_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_test_conditional():
    """Conditional drawing with animated expressions."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6, profiles=0)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2, FE.DIV)
        cy = rc.float_expression(h, 2, FE.DIV)
        rc.draw_round_rect(0, 0, w, h, 100, 100)
        rc.rc_paint.set_color(0xFFFFFF00).set_text_size(100.0).commit()
        rc.draw_text_anchored("expression in eval loop", cx, cy, 0.0, 0.0, 0)
        tick = rc.float_expression(
            rc.exp(Rc.Time.TIME_IN_SEC, 3, FE.MOD, 1, FE.SUB,
                   cx, cy, FE.MIN, FE.MUL, 10, FE.ADD),
            rc.anim(0.5, Rc.Animate.CUBIC_STANDARD | (1 << 12)))
        odd = rc.float_expression(
            rc.exp(Rc.Time.TIME_IN_SEC, 3, FE.MOD, 1, FE.SUB))
        rc.float_expression(Rc.Time.CONTINUOUS_SEC)
        rc.draw_rect(0, cy, tick, h)
        rc.add_debug_message(" color ", odd)

        rc.conditional_operations(Rc.Condition.GT, odd, 0.0)
        rc.rc_paint.set_color(0xFFFF0000).commit()
        rc.draw_circle(cx, cy, tick)
        rc.end_conditional_operations()

        rc.conditional_operations(Rc.Condition.LT, odd, 0.0)
        rc.rc_paint.set_color(0xFF00FF00).commit()
        rc.draw_circle(cx, cy, tick)
        rc.end_conditional_operations()
        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_flow_control_checks1():
    """Nested loops, conditionals, and debug messages."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6, profiles=0)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.draw_round_rect(0, 0, w, h, 64, 64)
        rc.add_debug_message(">>> simple loop:")
        i = rc.create_float_id()
        rc.loop(id_from_nan(i), 0.0, 1.0, 10.0, lambda:
            rc.add_debug_message("  >>> count", i))
        rc.add_debug_message(">>> nested loop:")
        k = rc.create_float_id()

        def nested_loop1():
            rc.add_debug_message("  >>> count", i)
            def inner1():
                rc.add_debug_message("        >>> count2",
                                     rc.float_expression(k, i, 100, FE.MUL, FE.ADD))
            rc.loop(id_from_nan(k), 0.0, 1.0, 3.0, inner1)

        rc.loop(id_from_nan(i), 0.0, 1.0, 3.0, nested_loop1)

        rc.conditional_operations(Rc.Condition.EQ, 3, 3)
        rc.add_debug_message(" >>> static Equality check")
        rc.end_conditional_operations()

        def nested_loop2():
            rc.add_debug_message("  >>> count", i)
            def inner2():
                rc.add_debug_message("        >>> count2",
                                     rc.float_expression(k, i, 100, FE.MUL, FE.ADD))
                rc.conditional_operations(Rc.Condition.EQ, 3, 3)
                rc.add_debug_message("        >>> static Equality check")
                rc.end_conditional_operations()
                rc.conditional_operations(Rc.Condition.EQ, 2, 3)
                rc.add_debug_message(
                    "        >>> static Equality FAIL should not see this")
                rc.end_conditional_operations()
            rc.loop(id_from_nan(k), 0.0, 1.0, 3.0, inner2)

        rc.loop(id_from_nan(i), 0.0, 1.0, 3.0, nested_loop2)

        ans = rc.float_expression(10, 10, FE.MUL, 10, FE.ADD)
        rc.conditional_operations(Rc.Condition.EQ, ans, 110)
        rc.add_debug_message(" >>> 10*10+10 = 110 ", ans)
        rc.end_conditional_operations()

        def nested_loop3():
            rc.add_debug_message("  >>> count", i)
            def inner3():
                rc.add_debug_message("        >>> count2",
                                     rc.float_expression(k, i, 100, FE.MUL, FE.ADD))
                rc.conditional_operations(Rc.Condition.EQ, k, i)
                rc.add_debug_message("        >>> static Equality check k = i", k)
                rc.end_conditional_operations()
                rc.conditional_operations(Rc.Condition.NEQ, k, i)
                rc.add_debug_message("        >>> static inequality check k != i", k)
                rc.end_conditional_operations()
            rc.loop(id_from_nan(k), 0.0, 1.0, 3.0, inner3)

        rc.loop(id_from_nan(i), 0.0, 1.0, 3.0, nested_loop3)

        def last_loop_body():
            tmp = rc.float_expression(i, 10, FE.MUL)
            rc.conditional_operations(Rc.Condition.EQ, 0.0,
                                      rc.float_expression(i, 15, FE.MOD))
            rc.add_debug_message(">>>>> i,15,MOD ", tmp)
            rc.end_conditional_operations()

        rc.loop(id_from_nan(i), 0.0, 1.0, 60.0, last_loop_body)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_flow_control_checks2():
    """Basic loop with conditional debug messages."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6, profiles=0)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()

        rc.draw_round_rect(0, 0, w, h, 64, 64)
        rc.add_debug_message(">>> simple loop:")
        i = rc.create_float_id()

        def loop_body():
            tmp = rc.float_expression(i, 10, FE.MUL)
            rc.conditional_operations(Rc.Condition.EQ, 0.0,
                                      rc.float_expression(i, 15, FE.MOD))
            rc.add_debug_message(">>>>> i,15,MOD ", tmp)
            rc.end_conditional_operations()

        rc.loop(id_from_nan(i), 0.0, 1.0, 60.0, loop_body)
        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)
