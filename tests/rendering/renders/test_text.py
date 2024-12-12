from command_line_assistant.rendering.decorators.colors import ColorDecorator
from command_line_assistant.rendering.decorators.style import StyleDecorator
from command_line_assistant.rendering.decorators.text import TextWrapDecorator
from command_line_assistant.rendering.renders.text import TextRenderer


def test_text_renderer_multiple_decorators():
    renderer = TextRenderer()
    renderer.update(ColorDecorator(foreground="red"))
    renderer.update(StyleDecorator("bright"))
    renderer.update(TextWrapDecorator(width=50))

    # Verify renderer has all decorators
    assert len(renderer._decorators) == 3


def test_text_renderer_decorator_override():
    renderer = TextRenderer()
    renderer.update(ColorDecorator(foreground="red"))
    renderer.update(ColorDecorator(foreground="blue"))

    # Verify last decorator of same type overrides previous
    assert len(renderer._decorators) == 1


def test_text_renderer_render_single_decorator(capsys):
    renderer = TextRenderer()
    renderer.update(ColorDecorator(foreground="red"))

    test_text = "Test message"
    renderer.render(test_text)

    captured = capsys.readouterr()
    assert test_text in captured.out


def test_text_renderer_render_multiple_decorators(capsys):
    renderer = TextRenderer()
    renderer.update(ColorDecorator(foreground="blue"))
    renderer.update(StyleDecorator("bright"))
    renderer.update(TextWrapDecorator(width=20))

    test_text = "This is a test message that should be wrapped"
    renderer.render(test_text)

    expected_text = (
        "\x1b[1m\x1b[34mThis is atest message thatshould bewrapped\x1b[0m\x1b[0m"
    )
    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    assert expected_text in "".join(lines)
    assert all(len(line) <= 20 for line in lines)


def test_text_renderer_render_empty_text(capsys):
    renderer = TextRenderer()
    renderer.update(ColorDecorator(foreground="green"))

    renderer.render("")

    captured = capsys.readouterr()
    # TODO(r0x0d): right now, we are still applying the color and everything else.
    # Maybe in the future we want to get rid of the formatting if we don't have text...
    assert captured.out.strip() == ""


def test_text_renderer_render_multiline(capsys):
    renderer = TextRenderer()
    renderer.update(ColorDecorator(foreground="yellow"))

    test_text = "Line 1\nLine 2\nLine 3"
    renderer.render(test_text)

    captured = capsys.readouterr()
    assert len(captured.out.strip().split("\n")) == 3
