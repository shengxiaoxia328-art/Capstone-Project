"""只用旧10个样本重跑 mimo，不跑新样本"""
import json, os

with open("benchmark_data_complete.json", "r", encoding="utf-8-sig") as f:
    all_samples = json.load(f)

old_samples = []
for s in all_samples:
    sid = os.path.splitext(os.path.basename(s.get("image_path", "")))[0]
    if sid != "升排长__照相馆":
        old_samples.append(s)
    else:
        print(f"  Excluded: {sid}")

print(f"Old samples: {len(old_samples)}")
for s in old_samples:
    sid = os.path.splitext(os.path.basename(s.get("image_path", "")))[0]
    print(f"  {sid}")

with open("benchmark_data_old10.json", "w", encoding="utf-8") as f:
    json.dump(old_samples, f, ensure_ascii=False, indent=2)
print("Saved benchmark_data_old10.json")
