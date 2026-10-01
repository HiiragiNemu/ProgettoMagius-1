# 剧情校订与累计贡献台账

核定快照：玩家剧情包 **3318**。Reader `0d04f7adc9db140a1f7fac1183c5d346353b7899`；CN patch `ed09e4b5b2a25968e7db51f8b3d78cec2c8e4423`；发行仓 `cf2b70fc2606801b574c3d4632daaf743def6d34`。

确认 AI／机翻来源的独立运行片段共 **1079**，全文复核 **347**，尚待 **732**（已含未索引 24）。完成中接手前已有 **48**，接手后 **299**；前一个 AI 的成果没有清零。

自 3301 至 3318 的已发布改动按运行 JSON 路径去重，共涉及 **635** 个片段。其中存在正文校订的 **317** 个片段、**10187** 个不同字段地址；历史重复校订计 **10187** 次操作，不能把操作次数当新句数。姓名修正、运行结构对齐和原稿恢复另列，不能都声称为原创翻译或全文复核。

## 固定文件与统计口径

`processed-runtime-scripts.tsv`：全部已发布修改的运行片段，含剧情 ID、标题、Reader 路径、首次／最近版本和累计版本；同一剧情镜像不重复计数。

`full-reviewed-ai-scripts.tsv` 与 `pending-ai-scripts.tsv`：逐片段完整复核／剩余清单，附当前中日文 blob、来源和复核证据。

`indexed-chapters.tsv`：整话与片段关系，区分触及部分片段、AI 部分完成、整话所有片段均有完整证据。

`batches.json`：接手前后每批发布数、原始报告口径、剧情列表和提交 SHA。`ledger.json.gz`：完整字段级前后文字、地址、历史事件、来源台账与发行回执；可用于核对实际贡献范围。

正文字段数是按当前JSON地址记录的显示字段修改数，并非新译句数。它也可能包含称呼、字词、文本错位归位、换行和标点修正；例如3309的102502-1_lDVQb存在台词与内嵌标签一起归位的历史记录，完整前后文字和same_executable_tags标志都已保留，不能据此声称新增了同等数量的原创翻译。

## 更早的历史登记同样保留

旧 `manual_retranslation/PROCESSED_STORY_TITLES.md` 登记 507 个候选条目、498 个唯一剧情 ID。原档不删除；本台账把 498 个 ID 全部保存在 `legacy-registered-stories.tsv`，去掉不同段落重复列举的条目。该旧档的“剩余 0”指译文写入和结构校验，不代表当前逐句质量审查已完成。不得与本台账的片段数直接相加，也不得据文件名中的“人工”重写原作者署名。

## 贡献署名边界

可据此核定维护者主导、AI 辅助的剧情校订、姓名规范、运行兼容、来源恢复与整合发布工作。原国服、官方、Wiki 和确认人工译者的原文贡献继续归原作者；本台账只记录实际新增改动与复核，不把保留的原译据为己有。具体展示署名由维护者确认，当前未修改游戏贡献 UI／APK。

另有 Reader 128 个与客户端独有 35 个正文仅属于来源调查；没有把未知来源自动算为 AI、待重译或已完成。43 份既有 V4 兼容和 196 份授权中文是保全范围，不因保全而新增翻译贡献数。

## 接手前后批次

| 版本 | 阶段 | 类型 | 修改片段 | 有正文校订片段 | 正文字段地址 | 数据提交 |
|---|---|---|---:|---:|---:|---|
| 3301 | 接手前 | text_correction | 14 | 14 | 956 | `8e02baee9e` |
| 3302 | 接手前 | text_correction | 4 | 0 | 0 | `f7d1736c17` |
| 3303 | 接手前 | text_correction | 8 | 7 | 487 | `30f2aefb06` |
| 3304 | 接手前 | text_correction | 7 | 7 | 512 | `7b8dc4495c` |
| 3305 | 接手前 | text_correction | 4 | 4 | 298 | `a45c6fc6f5` |
| 3306 | 接手前 | text_correction | 160 | 1 | 1 | `3c4439fc7a` |
| 3307 | 接手前 | text_correction | 27 | 4 | 294 | `c9fa878d33` |
| 3308 | 接手前 | text_correction | 19 | 7 | 222 | `3201c963cb` |
| 3309 | 接手前 | text_correction | 2 | 2 | 93 | `f280b61751` |
| 3310 | 接手前 | runtime_alignment | 130 | 0 | 0 | `149208c9a6` |
| 3311 | 接手前 | runtime_alignment_and_name | 12 | 0 | 0 | `54af872e57` |
| 3312 | 接手前 | source_restoration | 5 | 0 | 0 | `0982d3040c` |
| 3313 | 接手前 | text_correction | 5 | 5 | 405 | `bb7e164a45` |
| 3314 | 接手后 | text_correction | 30 | 30 | 1713 | `6e9965e76d` |
| 3315 | 接手后 | text_correction | 59 | 59 | 1800 | `39a0d94391` |
| 3316 | 接手后 | text_correction | 44 | 44 | 163 | `93305879d4` |
| 3317 | 接手后 | text_correction | 61 | 61 | 720 | `f1955c691d` |
| 3318 | 接手后 | text_correction | 72 | 72 | 2523 | `0d04f7adc9` |

各阶段修改片段合计需要扣除跨阶段重复：当前有 9 个运行片段在接手前后均有改动，累计总数已经去重。

## 后续维护

每批发布并完成当前来源核对后，用 `tools/story_quality_contributions.py` 重新生成以上记录。先刷新三仓 main 和已发布版本，固定 Reader、patch、public 引用；有并行改动或中日文 blob 漂移时必须中止核算并刷新来源。不得删除历史批次，不得只改汇总数字，未发布的暂存校订单独留在当前批次交接中。

示例：`python tools/story_quality_contributions.py --reader . --patch-git <patch.git> --public-git <public.git> --reader-ref <SHA> --patch-ref <SHA> --public-ref <SHA> --last-version 3318 --output <staging-directory>`。生成器只读 Git、只写指定报告目录，不触碰剧情与贡献展示。
