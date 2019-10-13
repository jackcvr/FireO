from fireo.fields.fields import ReferenceField
from fireo.queries import errors


class ModelWrapper:
    """Convert query result into Model instance"""
    @classmethod
    def from_query_result(cls, model, doc):
        if doc.to_dict() is None:
            return None

        for k, v in doc.to_dict().items():
            field = model._meta.get_field_by_column_name(k)
            # if missing field setting is set to "ignore" then
            # get_field_by_column_name return None So, just skip this field
            if field is None:
                continue
            # Check if it is Reference field
            if isinstance(field, ReferenceField):
                val = ReferenceFieldWrapper.from_doc_ref(field, field.field_value(v))
            else:
                # get field value
                val = field.field_value(v)
            setattr(model, field.name, val)
        setattr(model, '_id', doc.id)
        return model


class ReferenceFieldWrapper:
    """Get reference documents

    If auto_load is True then load the document otherwise return `ReferenceDocLoader` object and later user can use
    `get()` method to retrieve the document
    """
    @classmethod
    def from_doc_ref(cls, field, ref):
        if not ref:
            return None

        ref_doc = ReferenceDocLoader(field, ref)

        if field.auto_load:
            return ref_doc.get()
        return ref_doc


class ReferenceDocLoader:
    """Get reference doc and Convert into model instance"""
    def __init__(self, field, ref):
        self.field = field
        self.ref = ref

    def get(self):
        doc = self.ref.get()
        if not doc.exists:
            raise errors.ReferenceDocNotExist(f'{self.field.model_ref.collection_name}/{self.ref.id} not exist')
        return ModelWrapper.from_query_result(self.field.model_ref(), doc)
