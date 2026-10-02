/* Browser-local draft storage; no network, credentials, or font generation. */
(() => {
  /** Copy JSON-compatible settings so UI edits cannot mutate stored snapshots. */
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  /** Create the small document interface used by the existing Lab Save workflows. */
  function createLocalDB(key, storage) {
    /** Read this Lab's document map, rejecting malformed or unsupported records. */
    function read() {
      const raw = (storage || window.localStorage).getItem(key);
      if (!raw) return Object.create(null);
      const saved = JSON.parse(raw);
      if (!saved || saved.version !== 1 || !saved.documents || typeof saved.documents !== 'object' || Array.isArray(saved.documents)) {
        throw new Error('Invalid saved draft data');
      }
      return saved.documents;
    }
    /** Return an isolated document snapshot with the existing exists/data contract. */
    function snapshot(records, id) {
      const exists = Object.hasOwn(records, id);
      return {exists, data: () => exists ? clone(records[id]) : undefined};
    }
    return {
      local: true,
      doc: id => ({
        get: async () => snapshot(read(), id),
        set: async value => {
          const records = read();
          Object.defineProperty(records, id, {value:clone(value), enumerable:true, writable:true, configurable:true});
          (storage || window.localStorage).setItem(key, JSON.stringify({version:1, documents:records}));
        }
      }),
      collection: name => ({get: async () => {
        const records = read();
        const prefix = name + '/';
        return {docs:Object.keys(records).filter(id => id.startsWith(prefix)).map(id => snapshot(records, id))};
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
