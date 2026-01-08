import argparse
from pathlib import Path
import httpx
from graphql import (
    build_client_schema,
    get_introspection_query,
    is_enum_type,
    is_list_type,
    is_non_null_type,
    is_object_type,
    is_scalar_type,
)

def unwrap(t):
    while is_non_null_type(t) or is_list_type(t):
        t = t.of_type
    return t

def selection(t, depth, seen):
    named = unwrap(t)
    if not is_object_type(named):
        return None
    if named.name in seen:
        return "__typename"
    seen = seen | {named.name}
    fields = []
    for name, f in named.fields.items():
        ft = unwrap(f.type)
        if is_scalar_type(ft) or is_enum_type(ft):
            fields.append(name)
        elif depth > 0:
            sub = selection(f.type, depth - 1, seen)
            if sub:
                fields.append(f"{name} {{ {sub} }}")
    return " ".join(fields) if fields else "__typename"

def load_schema(url):
    resp = httpx.post(url, json={"query": get_introspection_query()})
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return build_client_schema(data["data"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", default="graphql/auto.graphql")
    ap.add_argument("--depth", type=int, default=1)
    args = ap.parse_args()

    schema = load_schema(args.url)
    ops = []

    for kind, root in (("query", schema.query_type), ("mutation", schema.mutation_type)):
        if not root:
            continue
        for fname, field in root.fields.items():
            var_defs = []
            var_args = []
            for aname, arg in field.args.items():
                if is_non_null_type(arg.type):
                    var_defs.append(f"${aname}: {arg.type}")
                    var_args.append(f"{aname}: ${aname}")
            vars_str = f"({', '.join(var_defs)})" if var_defs else ""
            args_str = f"({', '.join(var_args)})" if var_args else ""
            sel = selection(field.type, args.depth, set())
            body = f"{fname}{args_str}" + (f" {{ {sel} }}" if sel else "")
            ops.append(f"{kind} {kind}_{fname}{vars_str} {{ {body} }}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n\n".join(ops) + "\n", encoding="utf-8")
    print(f"Wrote {len(ops)} ops to {out}")

if __name__ == "__main__":
    main()