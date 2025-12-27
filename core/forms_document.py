from django import forms
from core.models import DocumentTemplateInput


def build_document_input_form(template_obj, post_data=None):
    """
    فرم داینامیک بر اساس DocumentTemplateInput
    """
    fields = {}

    for inp in template_obj.inputs.all():
        kwargs = {
            "label": inp.label,
            "required": inp.required,
            "initial": inp.default_value or "",
            "widget": forms.TextInput(attrs={"placeholder": inp.placeholder or ""}),
        }

        if inp.input_type == DocumentTemplateInput.TEXT:
            fields[inp.key] = forms.CharField(**kwargs)

        elif inp.input_type == DocumentTemplateInput.NUMBER:
            fields[inp.key] = forms.IntegerField(**kwargs)

        elif inp.input_type == DocumentTemplateInput.DATE:
            # تاریخ میلادی با input type date (ساده)
            kwargs["widget"] = forms.DateInput(attrs={"type": "date"})
            fields[inp.key] = forms.DateField(**kwargs)

        elif inp.input_type == DocumentTemplateInput.CHOICE:
            choices = []
            if inp.choices_text:
                for line in inp.choices_text.splitlines():
                    line = line.strip()
                    if line:
                        choices.append((line, line))
            kwargs["widget"] = forms.Select()
            fields[inp.key] = forms.ChoiceField(choices=choices, **kwargs)

    DynamicForm = type("DynamicDocInputForm", (forms.Form,), fields)

    if post_data is not None:
        return DynamicForm(post_data)
    return DynamicForm()
