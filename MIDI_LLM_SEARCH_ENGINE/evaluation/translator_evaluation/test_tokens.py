import json, random, sys, tempfile
from pathlib import Path
sys.path.insert(0, '.')
import evaluation_3_paraphrases as E
from midi_analyzer_tagger.extractors import PLUGINS
from midi_analyzer_tagger.analysis.registry import ExtractorRegistry
from midi_analyzer_tagger.exporters.taxonomy import TaxonomyExporter
from midi_analyzer_tagger.storage.sqlite import AnalysisDatabase
from midi_llm_search_engine.index_loader import SearchIndex
from midi_llm_search_engine.llm_client import LLMTranslator

material = json.loads(E.MATERIAL.read_text())
taxonomy = TaxonomyExporter(ExtractorRegistry(PLUGINS)).to_dict()
tmp = Path(tempfile.mkdtemp())
tax_path = tmp / 'taxonomy.json'
db_path = tmp / 'analysis.db'
tax_path.write_text(json.dumps(taxonomy, indent=2))
with AnalysisDatabase(db_path) as db:
    db.create_tables()
index = SearchIndex(db_path, tax_path)
translator = LLMTranslator(index, include_semantic_analysis=False)

# Build a combo 9 trial exactly like the eval does
rng = random.Random(E.SEED)
family = "drums"
active = E._active_concepts(taxonomy, material, family)
combo_active = [c for c in active if c != "metadata_instrument_family"]
combos = E._sample(combo_active, 9, 5, rng)
combo = combos[0]
chosen = [rng.choice(E._paraphrases_for(material, c, family)) for c in combo]
prompt = E._with_prefix_note(", ".join(e["paraphrase"] for e in chosen), family)

sys_prompt = translator.system_prompt
messages = [
    {"role": "system", "content": sys_prompt},
    {"role": "user", "content": f"Convert to concept targets: \"{prompt}\""},
]

# estimate prompt chars and rough token count
total_chars = sum(len(m.get("content","")) for m in messages)
print("concepts in combo:", len(combo))
print("system prompt chars:", len(sys_prompt))
print("query chars:", len(prompt))
print("total input chars:", total_chars, " (~rough tokens:", int(total_chars/4), ")")

# make ONE raw call, capture full response
resp = translator._chat(messages)
msg = resp.choices[0].message
content = msg.content or ""
print("\n--- response ---")
print("finish_reason:", resp.choices[0].finish_reason)
print("content empty?:", content.strip() == "")
print("content length:", len(content))
print("content head:", repr(content[:150]))
try:
    print("usage:", resp.usage)
except Exception as e:
    print("usage err:", e)
