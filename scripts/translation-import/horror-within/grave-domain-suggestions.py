import json
from weblate.trans.models import Suggestion
ids=[126028, 125879, 125842, 125885, 125902, 125903, 125853, 125854, 125855, 125856, 125857, 125859, 125860]
print("GRAVE_SUGGESTIONS_JSON="+json.dumps({"suggestions":[{"id":s.id,"unit_id":s.unit_id,"target":[s.target] if isinstance(s.target,str) else list(s.target)} for s in Suggestion.objects.filter(unit_id__in=ids)]},ensure_ascii=False))
