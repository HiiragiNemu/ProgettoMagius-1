# MAGIA 客户端与运行资源

## 正式客户端 1.6.3（构建号 1713001030）

本项目继续更新仓库，并同步正式 APK、资源包与完整对应源码；仓库公开或私有状态调整不代表停止维护。

- [下载正式 APK](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magireco-legacy-client-1.6.3-b1713001030.apk)
- [下载本构建对应源码与构建材料](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magia-1.6.3-b1713001030-four-profile-corresponding-source-7e2e543b.zip)
- [签名版本信息](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magireco-legacy-client-1.6.3-b1713001030.version.json)
- [文件清单与 SHA-256](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magia-1.6.3-github-release-manifest.json) · [SHA256SUMS](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magia-1.6.3-github-SHA256SUMS.txt)

对应源码固定于提交 `7e2e543baa31cce2a623058bbd20640a9fbdc9ad`；源码包包含对应版权、许可与构建说明。维护选项为 1.6.3 / 1.6.2 / 1.6.1 / 1.6.0，均绑定同一维护索引。

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| APK | 138352485 | `5715af939db509e2a82ca2436085a9f371aad0ca0e3a4c403d9937463852aa17` |
| 对应源码 ZIP | 480309975 | `b9d88e839dbe2b1f52d99f6da403981a251b4b23bbca1645b9c7e039c4cd1d47` |
| 四档维护索引 | 9174 | `3294503a745bcac07d0fbef5a15d1473d74635341a6ef293926ef93f20b024c4` |

### 本次修复

- 1.6.3 累计修复；覆盖安装保留已有存档、字体和资源。
- 修正本地相机入口的接口绑定，调整拍照请求的可选 EXIF 缩略图设置；实际拍摄由手机端确认。
- 修正御魂的特训页签绘制，保留原活动条件与网络接口。
- 修正记忆图片的按需加载、万圣节队伍缓存字段、属性强化的属性数值刷新及结果窗口重复创建；保留已有角色、道具、奖励和记录。
- 诊断导出补充当前受管理存档的既有诊断信息，不改写存档；此项不代表新增玩法修复。
- Magia Clash 的 SINGLERAID 原始数据缺口及2019年蓝宝石故障原因仍待解决，不计入本次已解决事项。

- 补齐本地队伍编成页首次初始化所需的两项角色强化集合；已核对冷进入编成、返回关卡页、活动首页及主页。
- 队伍战力 NaNPt 显示仍待处理；批量材料操作及手机实际拍摄仍待对应验证，不列为本轮已验收。

### 配对资源

- [前端完整资源 v105](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/cn_js_update_v2.full105-v105.zip)。
- [累计修订 v67](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/cn_js_delta_v2.delta67.zip)。
- [离线数据 Pack17 v10](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/cn_offline_update.zip)。
- [最终资源补丁 Pack18 v16](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/cn_offline_delta.zip)。

版本元数据、清单和归档身份按本次文件清单配对。历史不可变资产继续保留；当前泛名入口以本次签名元数据为准。请使用与实际 APK 匹配的对应源码。

[全部发行资产](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/tag/latest)

`resource-manifest.json` 为原有资源保留清单，不代表最新推荐版本；当前正式文件以本页和上述发行清单为准。
