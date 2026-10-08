import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const hooks = new Map();
let initializeItem;
class DataModel { toObject() { return this.source; } }
globalThis.Hooks = { on: (name, fn) => hooks.set(name, fn) };
globalThis.game = {
  system: { id: 'dnd5e' },
  settings: { register() {}, get: () => false },
  babele: { registerConverters() {} }
};
globalThis.foundry = { abstract: { DataModel } };
globalThis.dnd5e = { utils: {
  // Enough of Foundry's strict slugify for these ASCII/Chinese fixtures.
  formatIdentifier: text => text.toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-|-$/g, '')
} };
globalThis.libWrapper = {
  register(module, target, wrapper, type) {
    assert.equal(module, 'dnd-contents-zh-tw');
    assert.equal(target, 'CONFIG.Item.documentClass.prototype._initializeSource');
    assert.equal(type, 'WRAPPER');
    initializeItem = wrapper;
  }
};
await import('../register.js');
hooks.get('init')();

const bookId = 'hY0c3vxHK35KTTxp';
const activityId = '5qVxZoKDUruKL2Ts';
const makeBook = () => ({ _id: bookId, type: 'equipment', name: '法術書',
  system: { identifier: '', activities: { [activityId]: { type: 'cast' } } } });
const makeSpell = () => ({ _id: 'Vy6OkLLu3Ewi0glo', type: 'spell', name: '完全復活術',
  system: { identifier: 'true-resurrection', sourceItem: 'equipment:' },
  flags: { dnd5e: { cachedFor: `.Item.${bookId}.Activity.${activityId}` } } });
const initialize = (source, actorSource) => {
  assert.equal(typeof initializeItem, 'function', 'register an initialization wrapper before world documents load');
  const options = { parent: actorSource ? { _source: actorSource } : undefined };
  return initializeItem.call({}, (data, passedOptions) => {
    assert.equal(passedOptions, options);
    return data;
  }, source, options);
};

test('repair the captured equipment: failure using its cachedFor source', () => {
  const book = makeBook();
  const spell = initialize(makeSpell(), { items: [book] });
  const preparedBook = initialize(structuredClone(book));
  assert.match(preparedBook.system.identifier, /^[a-z0-9_-]+$/i);
  assert.equal(spell.system.sourceItem, `equipment:${preparedBook.system.identifier}`);
  assert.equal(spell.system.identifier, 'true-resurrection');
  assert.equal(preparedBook.name, '法術書');
  assert.equal(book.system.identifier, '', 'do not mutate the parent source while preparing its child');
});

test('preserve original English identity when a translated item has an empty identifier', () => {
  const item = makeBook();
  item.flags = { babele: { originalName: 'Spellbook' } };
  assert.equal(initialize(item).system.identifier, 'spellbook');
});

test('preserve configured identifiers and healthy source links', () => {
  const book = makeBook(); book.system.identifier = 'custom-spellbook';
  const spell = makeSpell(); spell.system.sourceItem = 'class:wizard';
  assert.equal(initialize(book).system.identifier, 'custom-spellbook');
  assert.equal(initialize(spell, { items: [book] }).system.sourceItem, 'class:wizard');
});

test('leave an ambiguous or missing source unchanged', () => {
  const spell = makeSpell(); delete spell.flags;
  assert.equal(initialize(spell, { items: [makeBook()] }).system.sourceItem, 'equipment:');
  assert.equal(initialize(makeSpell(), { items: [] }).system.sourceItem, 'equipment:');
  const wrongType = makeBook(); wrongType.type = 'feat';
  assert.equal(initialize(makeSpell(), { items: [wrongType] }).system.sourceItem, 'equipment:');
  const wrongActivity = makeBook(); wrongActivity.system.activities[activityId].type = 'attack';
  assert.equal(initialize(makeSpell(), { items: [wrongActivity] }).system.sourceItem, 'equipment:');
});

test('normalize DataModel input and keep the fallback stable after a rename', () => {
  const model = new DataModel(); model.source = makeBook();
  const item = initialize(model);
  const id = item.system.identifier;
  item.name = '另一個名字';
  assert.equal(initialize(item).system.identifier, id);
});

const lang = JSON.parse(readFileSync(new URL('../lang/zh-tw.json', import.meta.url), 'utf8'));
const inline = lang['EDITOR.DND5E.Inline'];
const format = (template, data) => template.replace(/\{([^{}]+)\}/g, (_, key) => data[key]);
test('damage templates retain their caller placeholders and the clickable link', () => {
  const expected = { DamageAverage: ['average', 'formula', 'type'], DamageShort: ['formula', 'type'],
    DamageDouble: ['first', 'second'], DamageLong: ['damage'], DamageExtended: ['damage'] };
  for (const [key, placeholders] of Object.entries(expected)) {
    assert.deepEqual([...inline[key].matchAll(/\{([^{}]+)\}/g)].map(m => m[1]).sort(), placeholders.sort(), key);
  }
  const link = '<a data-action="roll" data-formulas="2d6">7 (2d6) 鈍擊</a>';
  const long = format(inline.DamageLong, { damage: link });
  const extended = format(inline.DamageExtended, { damage: long });
  assert.ok(extended.includes(link));
  assert.ok(!extended.includes('undefined'));
  assert.equal((extended.match(/傷害/g) ?? []).length, 1);
});

test('the manifest and release archive include the language file', () => {
  const manifest = JSON.parse(readFileSync(new URL('../module.json', import.meta.url), 'utf8'));
  assert.ok(manifest.languages.some(l => l.lang === 'zh-tw' && l.path === 'lang/zh-tw.json'));
  assert.ok(manifest.relationships.requires.some(r => r.id === 'lib-wrapper'));
  const workflow = readFileSync(new URL('../.github/workflows/release.yml', import.meta.url), 'utf8');
  assert.match(workflow, /cp\s+lang\/zh-tw\.json\s+dist\/dnd-contents-zh-tw\/lang\//);
});
