/* Browser-local draft storage; no network, credentials, or font generation. */
(() => {
  /** Copy JSON-compatible settings so UI edits cannot mutate stored snapshots. */
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  /** Create the small document interface used by the existing Lab Save workflows. */
  function createLocalDB(key, storage) {
    const prefix = key + ':doc:';
    /** Parse a storage record without replacing malformed or unsupported data. */
    function parse(raw) {
      try { return JSON.parse(raw); }
      catch { throw new Error('Invalid saved draft data'); }
    }
    /** Read the original single-map format for drafts saved before per-document storage. */
    function legacy() {
      const raw = (storage || window.localStorage).getItem(key);
      if (raw === null) return Object.create(null);
      const saved = parse(raw);
      if (!saved || saved.version !== 1 || !saved.documents || typeof saved.documents !== 'object' || Array.isArray(saved.documents)) {
        throw new Error('Invalid saved draft data');
      }
      return saved.documents;
    }
    /** Read one draft, preferring its dedicated key over the retained original map. */
    function readDocument(id) {
      const raw = (storage || window.localStorage).getItem(prefix + encodeURIComponent(id));
      if (raw !== null) {
        const saved = parse(raw);
        if (!saved || saved.version !== 1 || !saved.document || typeof saved.document !== 'object' || Array.isArray(saved.document)) {
          throw new Error('Invalid saved draft data');
        }
        return {exists:true, value:saved.document};
      }
      const records = legacy();
      const exists = Object.hasOwn(records, id), value = records[id];
      if (exists && (!value || typeof value !== 'object' || Array.isArray(value))) {
        throw new Error('Invalid saved draft data');
      }
      return {exists, value};
    }
    /** Return an isolated document snapshot with the existing exists/data contract. */
    function snapshot(record) {
      return {exists:record.exists, data: () => record.exists ? clone(record.value) : undefined};
    }
    return {
      local: true,
      doc: id => ({
        get: async () => snapshot(readDocument(id)),
        set: async value => {
          // Reject corrupt existing data; never erase another document's saved value.
          readDocument(id);
          (storage || window.localStorage).setItem(prefix + encodeURIComponent(id), JSON.stringify({version:1, document:clone(value)}));
        }
      }),
      collection: name => ({get: async () => {
        const store = storage || window.localStorage;
        const ids = new Set(Object.keys(legacy()));
        for (let i = 0; i < store.length; i++) {
          const storedKey = store.key(i);
          if (storedKey && storedKey.startsWith(prefix)) ids.add(decodeURIComponent(storedKey.slice(prefix.length)));
        }
        return {docs:[...ids].filter(id => id.startsWith(name + '/')).map(id => snapshot(readDocument(id))).filter(doc => doc.exists)};
      }})
    };
  }
  /** Download portable settings even when clipboard or browser storage is unavailable. */
  function downloadJSON(value, filename) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2) + '\n'], {type:'application/json'}));
    const link = document.createElement('a');
    link.href = url; link.download = filename;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  window.SEIHouseDrafts = {createLocalDB, downloadJSON};
})();
