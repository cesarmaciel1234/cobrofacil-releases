import os
import filecmp

def compare_dirs(dir1, dir2):
    diffs = []
    for root, _, files in os.walk(dir1):
        for f in files:
            p1 = os.path.join(root, f)
            p2 = p1.replace(dir1, dir2, 1)
            if not os.path.exists(p2):
                diffs.append(f"Missing in {dir2}: {p1}")
            else:
                if not filecmp.cmp(p1, p2, shallow=False):
                    diffs.append(f"Different: {p1}")
    return diffs

d = compare_dirs('extract_tmp/src/carteleria/lanzador_tv/la_cara_web', 'src/carteleria/lanzador_tv/la_cara_web')
print(f"Found {len(d)} differences in la_cara_web:")
for x in d: print(x)
