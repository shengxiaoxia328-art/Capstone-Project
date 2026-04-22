"""
构建真实数据集 benchmark_data_real.json
- 8个样本复用已有照片任务（照片相同）
- 镇长上任使用新照片（镇长上任__机关门口.png），需新建tasks
- 检察官上任、师生情泛黄为全新样本，需新建tasks
"""
import json
import os

BASE = "d:/desktop/Tencent Capstone Project"
REAL = f"{BASE}/腾讯数据"

# 加载已有 benchmark
with open(f"{BASE}/benchmark_data_complete.json", "r", encoding="utf-8") as f:
    old_samples = json.load(f)

# 建立已有样本索引 (by short name)
old_index = {}
for s in old_samples:
    # 从 image_path 提取短名
    name = os.path.basename(s["image_path"]).replace(".png", "")
    old_index[name] = s

# ============ 真实数据文件映射 ============
# 成文和访谈文件名
real_samples_config = [
    {
        "name": "军营代笔__集体照",
        "memoir": "军营代笔__集体照.txt",
        "interview": "军营代笔__集体照.txt",
        "photo": "军营代笔__集体照.png",
        "reuse_photo_from": "军营代笔__集体照",
    },
    {
        "name": "升排长__照相馆",
        "memoir": "升排长__照相馆.txt",
        "interview": "升排长__照相馆访谈.txt",
        "photo": "升排长__照相馆.png",
        "reuse_photo_from": "升排长__照相馆",
    },
    {
        "name": "夜里行军",
        "memoir": "夜里行军.txt",
        "interview": "夜里行军.txt",
        "photo": "夜里行军.png",
        "reuse_photo_from": "夜里行军",
    },
    {
        "name": "宗祠",
        "memoir": "宗祠.txt",
        "interview": "宗祠.txt",
        "photo": "宗祠.png",
        "reuse_photo_from": "宗祠",
    },
    {
        "name": "射击比赛第一名",
        "memoir": "射击比赛第一名.txt",
        "interview": "射击比赛第一名.txt",
        "photo": "射击比赛第一名.png",
        "reuse_photo_from": "射击比赛第一名",
    },
    {
        "name": "知青下乡__集体照",
        "memoir": "知青下乡__集体照.txt",
        "interview": "知青下乡__集体照.txt",
        "photo": "知青下乡__集体照.png",
        "reuse_photo_from": "知青下乡__集体照",
    },
    {
        "name": "重返南澳岛",
        "memoir": "重返南澳岛.txt",
        "interview": "重返南澳岛.txt",
        "photo": "重返南澳岛.png",
        "reuse_photo_from": "重返南澳岛",
    },
    {
        "name": "难忘的演讲",
        "memoir": "难忘的演讲.txt",
        "interview": "难忘的演讲.txt",
        "photo": "难忘的演讲.png",
        "reuse_photo_from": "难忘的演讲",
    },
    # ===== 镇长上任：不同照片，需新 tasks =====
    {
        "name": "镇长上任",
        "memoir": "镇长上任.txt",
        "interview": "镇长上任.txt",
        "photo": "镇长上任__机关门口.png",
        "reuse_photo_from": None,  # 新照片
    },
    # ===== 全新样本 =====
    {
        "name": "检察官上任",
        "memoir": "检察官上任.txt",
        "interview": "检察官上任.txt",
        "photo": "检察官上任.png",
        "reuse_photo_from": None,
    },
    {
        "name": "师生情泛黄",
        "memoir": "师生情泛黄.txt",
        "interview": "师生情泛黄.txt",
        "photo": "师生情泛黄.png",
        "reuse_photo_from": None,
    },
]

# ============ 3个新照片的 tasks（从JSON文件加载）============
with open(f"{BASE}/new_photo_tasks.json", "r", encoding="utf-8") as f:
    new_photo_data = json.load(f)

# ============ 构建真实数据集 ============
real_benchmark = []

for cfg in real_samples_config:
    sample = {
        "interview_path": f"{REAL}/访谈数据/{cfg['interview']}",
        "memoir_path": f"{REAL}/成文数据/{cfg['memoir']}",
        "image_path": f"{REAL}/照片数据/{cfg['photo']}",
    }

    if cfg["reuse_photo_from"] is not None:
        # 复用已有 benchmark 的照片 tasks
        old = old_index[cfg["reuse_photo_from"]]
        sample["image_description"] = old["image_description"]
        sample["mme_tasks"] = old["mme_tasks"]
        sample["mmbench_tasks"] = old["mmbench_tasks"]
        sample["hooks"] = old["hooks"]
    else:
        # 使用新建的 tasks
        npd = new_photo_data[cfg["name"]]
        sample["image_description"] = npd["image_description"]
        sample["mme_tasks"] = npd["mme_tasks"]
        sample["mmbench_tasks"] = npd["mmbench_tasks"]
        sample["hooks"] = npd["hooks"]

    real_benchmark.append(sample)

# 验证所有文件均存在
missing = []
for i, s in enumerate(real_benchmark):
    for key in ["interview_path", "memoir_path", "image_path"]:
        p = s[key]
        if not os.path.exists(p):
            missing.append(f"样本{i} ({key}): {p}")

if missing:
    print("❌ 缺失文件:")
    for m in missing:
        print(f"  {m}")
else:
    print(f"✅ 全部 {len(real_benchmark)} 个样本文件验证通过")

# 写入
out_path = f"{BASE}/benchmark_data_real.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(real_benchmark, f, ensure_ascii=False, indent=4)
print(f"✅ 已生成 {out_path}")
print(f"   共 {len(real_benchmark)} 个样本")

# 对比信息
old_names = set(os.path.basename(s["image_path"]).replace(".png","") for s in old_samples)
real_names = set(cfg["name"] for cfg in real_samples_config)
print(f"\n仿真独有: {old_names - real_names}")
print(f"真实独有: {real_names - old_names}")
print(f"重叠样本: {old_names & real_names}")
