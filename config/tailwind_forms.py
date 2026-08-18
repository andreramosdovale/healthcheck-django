"""Aplica as classes Tailwind do componente `c-input`/`c-select` (shadcn_django)
aos widgets de qualquer ModelForm/Form, sem precisar reescrever cada campo
manualmente nos templates."""

from django import forms

INPUT_CLASSES = (
    "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 "
    "text-sm shadow-xs transition-colors placeholder:text-muted-foreground "
    "focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring "
    "disabled:cursor-not-allowed disabled:opacity-50"
)

CHECKBOX_CLASSES = "h-4 w-4 rounded border-input text-primary focus:ring-1 focus:ring-ring"


class TailwindFormMixin:
    """Mixin: aplica as classes do design system a todos os campos do form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{CHECKBOX_CLASSES} {existing}".strip()
            else:
                widget.attrs["class"] = f"{INPUT_CLASSES} {existing}".strip()
