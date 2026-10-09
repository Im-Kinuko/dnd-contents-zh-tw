import json
from weblate.trans.models import Suggestion
ids=[121981, 121982, 121983, 121984, 121986, 121987, 121988, 121989, 121096, 121097, 121098, 121099, 121307, 121308, 121309, 121310]
print("WARLOCK_SUGGESTIONS_JSON="+json.dumps({"suggestions":[{"id":s.id,"unit_id":s.unit_id,"target":list(s.target),"user_id":s.user_id} for s in Suggestion.objects.filter(unit_id__in=ids)]},ensure_ascii=False))
