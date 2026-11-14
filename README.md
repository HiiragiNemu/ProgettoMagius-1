# MAGIA 客户端与运行资源

## 正式客户端 1.6.1（构建号 1713001028）

GitHub 继续同步正式客户端、完整对应源码和已批准的资源文件。此前“APK 与客户端对应源码已停止公开分发”的说明已撤回。

- [下载正式 APK](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magireco-legacy-client-1.6.1-b1713001028.apk)
- [下载本构建对应源码与构建材料](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magia-1.6.1-b1713001028-four-profile-corresponding-source-1aa74989.zip)
- [签名版本信息](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magireco-legacy-client-1.6.1-b1713001028.version.json)
- [文件清单与 SHA-256](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magia-1.6.1-github-release-manifest.json) · [SHA256SUMS](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/magia-1.6.1-github-SHA256SUMS.txt)

对应源码固定于提交 `1aa749897e9462d1ccadfcd2d9bceb05ea18da39`；源码包内包含相应版权、许可和构建说明。本次发布配对使用已签名并固定身份的 APK、对应源码和四档维护索引，不在发布阶段另行重建。

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| APK | 139864012 | `a0b865ffb1f1b4f79be9bf31b69606d8f8d93da0d16963d03a59897ebb396808` |
| 对应源码 ZIP | 384942703 | `318be0746edfaba6aa6ef2cf8b5520925bb6af372df25cb68c3090f12053fbb6` |
| 四档维护索引 | 9174 | `a6bdda55e79033e541dd1a788f26b3ead54e6c6a5e69f36ff6cb3dcbe1119dc7` |

### 本次修复

- 1.6.1 累计修复；覆盖安装保留已有存档、字体和资源。
- 修复手动导入后的基础资源状态复核与后续增量衔接，避免使用版本检查前的旧安装状态。
- 统一最终资源生成与第18包精确选择顺序，保留已验证资源及公开接口。
- 修复万圣节活动阶段页未取得已保存队伍列表时的展示异常。
- 修复已核对的本地镜层冻结对手档案读取404；不改变在线路径、结算或奖励规则。

自动再战 409 与可选 recoveredstory 恢复不在本次发布范围。以上为本次修复与文件配对范围，不代表全游戏验收完成；发布后的原生更新查询仍须按验收记录核对。

### 配对资源

- [前端完整资源 v105](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/cn_js_update_v2.full105-v105.zip)。
- [累计修订 v67](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/cn_js_delta_v2.delta67.zip)。
- [离线数据 Pack17 v10](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/cn_offline_update.zip)。
- [最终资源补丁 Pack18 v14](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/download/latest/cn_offline_delta.zip)。

各包的版本元数据、文件清单和归档身份一并配对，详见本次文件清单。历史 Pack18 资产仅供追溯，不应当作当前推荐版本。

历史不可变版本资产继续保留；当前泛名入口以本次签名版本信息及文件清单为准。完整历史开发记录不是本页的下载替代品，请使用上方与实际 APK 匹配的对应源码。

[全部发行资产](https://github.com/HiiragiNemu/ProgettoMagius-1/releases/tag/latest)

`resource-manifest.json` 为原有资源保留清单，不代表最新推荐版本；当前正式文件以本页和上述发行清单为准。
