"""
Comprehensive integration validation for the AMCACI video pipeline.
Checks syntax, imports, scope variables, and cross-file consistency.
"""
import ast
import re
import sys

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
WARN = "\033[93m[WARN]\033[0m"

issues = []

def check(cond, label, fatal=True):
    if cond:
        print(f"{PASS}  {label}")
    else:
        tag = FAIL if fatal else WARN
        print(f"{tag}  {label}")
        issues.append((fatal, label))

# ─── 1. Syntax check ────────────────────────────────────────────────────────
print("\n=== 1. SYNTAX ===")
files = {
    "streamlit_page.py": None,
    "src/models/schemas.py": None,
    "src/utils/file_utils.py": None,
    "src/handlers/pipeline_handler.py": None,
    "src/services/video_processor.py": None,
    "src/services/clusterer.py": None,
    "src/services/agent1.py": None,
}
for fpath in files:
    try:
        src = open(fpath, encoding="utf-8").read()
        ast.parse(src)
        files[fpath] = src
        check(True, f"Syntax OK: {fpath}")
    except SyntaxError as e:
        check(False, f"Syntax ERROR {fpath}: line {e.lineno} — {e.msg}")

# ─── 2. schemas.py checks ───────────────────────────────────────────────────
print("\n=== 2. SCHEMAS ===")
schemas = files["src/models/schemas.py"] or ""
check("class FrameInfo" in schemas,           "FrameInfo class exists")
check("class VideoResult" in schemas,         "VideoResult class exists")
check("video_results" in schemas,             "PipelineState has video_results field")
check("frame_type: str" in schemas,           "FrameInfo.frame_type field exists")
check("summary_video_path: str" in schemas,   "VideoResult.summary_video_path field exists")

# ─── 3. file_utils.py checks ────────────────────────────────────────────────
print("\n=== 3. FILE_UTILS ===")
fu = files["src/utils/file_utils.py"] or ""
check('"video"' in fu,       '"video" subdir added to ensure_output_dirs')

# ─── 4. video_processor.py checks ───────────────────────────────────────────
print("\n=== 4. VIDEO_PROCESSOR ===")
vp = files["src/services/video_processor.py"] or ""
check("def merge_segments" in vp,                  "merge_segments() defined")
check("def match_summary_to_timestamps" in vp,     "match_summary_to_timestamps() defined")
check("def extract_3_frames_per_sentence" in vp,   "extract_3_frames_per_sentence() defined")
check("def extract_summary_video" in vp,           "extract_summary_video() defined")
check("def process_video_pipeline" in vp,          "process_video_pipeline() defined")
check("from src.models.schemas import" in vp,      "imports from schemas")
check("FrameInfo" in vp,                           "FrameInfo used in video_processor")
check("VideoResult" in vp,                         "VideoResult used in video_processor")
check("cv2.VideoCapture" in vp,                    "cv2.VideoCapture used")
check("VideoFileClip" in vp,                       "moviepy VideoFileClip imported")
check("concatenate_videoclips" in vp,              "moviepy concatenate_videoclips imported")
check("clip.close()" in vp,                        "Memory cleanup (.close()) present")

# ─── 5. pipeline_handler.py checks ──────────────────────────────────────────
print("\n=== 5. PIPELINE_HANDLER ===")
ph = files["src/handlers/pipeline_handler.py"] or ""
check("from src.services.video_processor import process_video_pipeline" in ph,
      "video_processor import present")
check("Stage 8" in ph,                              "Stage 8 block present")
check("video_processing" in ph,                    "video_processing event emitted")
check("apply_relabel_and_cluster" in ph,           "apply_relabel_and_cluster used")
check("base_labels" in ph,                         "base_labels cached and used")
check("cumulative_relabel" in ph,                  "cumulative_relabel dict present")
check("merge_pairs" in ph,                         "merge_pairs handled")
check("prev_score_sig" in ph,                      "Frozen-score early exit logic present")
# check Stage 8 comes AFTER state.completed = True not before
stage8_pos = ph.find("# Stage 8")
completed_pos = ph.find("state.completed = True")
check(stage8_pos < completed_pos,                  "Stage 8 runs BEFORE state.completed = True")

# ─── 6. streamlit_page.py checks ────────────────────────────────────────────
print("\n=== 6. STREAMLIT_PAGE ===")
sp = files["streamlit_page.py"] or ""
check("stage_complete.*video_processing" in sp or
      'data.get("stage") == "video_processing"' in sp,
      "video_processing callback handler present")
check("process_video_pipeline" in sp,   "process_video_pipeline called in Stage 8 UI")
check("dirs[\"video\"]" in sp or "dirs['video']" in sp,
      "video output dir used in Stage 8 UI")
check("st.video" in sp,                 "st.video() used in render_summary_card")
check("Extracted Keyframes" in sp,      "Keyframes expander present")
check("video_result" in sp,             "video_result param wired into render_summary_card")
check("video_results" in sp,            "video_results session state stored and read")

# Check that asdict is imported where Stage 8 UI uses it
# The Stage 8 block uses asdict(v)
stage8_ui_pos = sp.find("# Stage 8: Video Processing")
asdict_import_pos = sp.rfind("from dataclasses import asdict", 0, stage8_ui_pos)
check(asdict_import_pos > 0 or "asdict" in sp[:stage8_ui_pos],
      "asdict imported before Stage 8 UI block", fatal=False)

# Check that clusters variable is in scope for Stage 8
# clusters is defined in Stage 5 with: clusters = state_holder["clusters"]
clusters_in_scope = "state_holder[\"clusters\"]" in sp and \
                    sp.find("state_holder[\"clusters\"]") < stage8_ui_pos
check(clusters_in_scope,
      "clusters accessible via state_holder in Stage 8 scope", fatal=False)

# Check that video_path is in scope for Stage 8
vp_scope = sp.find("video_path") < stage8_ui_pos
check(vp_scope, "video_path in scope before Stage 8 UI block")

# Check None-safe guards
check("(instructions.get(\"relabel_suggestions\") or {})" in sp,
      "relabel_suggestions None-guard in streamlit")
check("(instructions.get(\"merge_pairs\") or [])" in sp,
      "merge_pairs None-guard in streamlit")
check("(metrics.failure_reasons or [])" in sp,
      "failure_reasons None-guard in streamlit")

# ─── 7. agent1.py checks ────────────────────────────────────────────────────
print("\n=== 7. AGENT1 ===")
a1 = files["src/services/agent1.py"] or ""
check('if result.get("merge_pairs") is None' in a1,
      "merge_pairs normalised to [] in agent1")
check('if result.get("relabel_suggestions") is None' in a1,
      "relabel_suggestions normalised to {} in agent1")

# ─── 8. clusterer.py checks ─────────────────────────────────────────────────
print("\n=== 8. CLUSTERER ===")
cl = files["src/services/clusterer.py"] or ""
check("def apply_relabel_and_cluster" in cl,   "apply_relabel_and_cluster defined")
check("def cluster_and_categorize" in cl,      "cluster_and_categorize defined")
# Check it returns 3 values
check("return clusters, integer_labels, base_refined_labels" in cl or
      "return clusters, labels, base_labels" in cl,
      "cluster_and_categorize returns 3-tuple")

# ─── Summary ─────────────────────────────────────────────────────────────────
print("\n=== SUMMARY ===")
fatal_issues   = [l for fatal, l in issues if fatal]
warning_issues = [l for fatal, l in issues if not fatal]

if not issues:
    print("All checks passed -- integration looks correct.")
else:
    if fatal_issues:
        print(f"\n{len(fatal_issues)} FATAL issue(s):")
        for l in fatal_issues:
            print(f"  FAIL: {l}")
    if warning_issues:
        print(f"\n{len(warning_issues)} warning(s):")
        for l in warning_issues:
            print(f"  WARN: {l}")

sys.exit(len(fatal_issues))
