# CRP F0074 — 正式VME启动产物一致性

## 整体计划与启动（2026-10-20）

用户“提交，继续”确认F0057/F0058/F0059并授权实际提交后一个单元；实际root a92ccf9，10文件653增88删，实际路径/mode/blob核对，87保留身份/379既有终检复用。根工作树/index干净；nested8101fad内容/index干净、850原mode保持。当前只做F0074，不恢复旧连续提交授权，不push/安装/M2推进。

目标/范围：关闭当前正式盘nterm非VME地址与HAS_VME冲突。记录现状/实际生成链，用已有nanos目录make ARCH=riscv64-nemu update→run建立同版ELF/文件表/盘/内核及实际消费者证据；如果仅旧资产则更新正式忽略产物，不硬造源码修改；若发现真实依赖失效则限于既有Make接口最小修复。历史错配的生成来源不猜测，原119项审阅记录不重写。

阶段/交付：本组一个独立单元，复用CRP整体计划/流程，不占业务Phase。先固定正式旧盘/ELF/链接/源码身份并核清VME传播和增量链接依赖；必要的当前严格loader动态拒绝见证；然后正常update，无额外clean，正式run验证三前台和后台hello。交付前后身份/运行命令和退出码、记录索引、唯一下一入口；有源码变化才附实际完整diff/语句解释/正反应用，无源码则明确资产修复与Git持久化边界。

验收：旧108连续extent/48ELF仅nterm不合用户域；标准update成功并确实更新正式安装ELF/文件表/盘，四启动ELF入口与段、全部ELF几何/文件范围/用户栈边界及盘内字节身份吻合；正式make run使用该内核/盘，PAL/NTerm/NSlider切换、命令响应与hello持续进展，目视真实SDL帧。选择CPU/RT/REF不消费本次Navy资产故不重跑，NPC/其他ISA不在本组验收内。固定最终源码/产物身份，确认无隐含commit/配置漂移。

停点：完成本组验证、目视、记录及一次性产物清理后停止，等待结果确认/提交；仅正式更新产物保留，旧盘不额外复制。真实策略/失败契约冲突、下载/安装即停；不通过额外clean改变用户流程。既有标准入口/归档/清理按CRP workflow；旧镜像的准确源码/flags Unknown，身份可查，不承诺逐字节重建该历史二进制。等价错配可从本组commit在隔离环境以现有非VME链接地址构造。

## 实施结果 — Completed，正式产物已更新，结果确认/文档commit Pending

本组F0074按既有正式update→run闭合，没有生产源码/Make接口修改。累计68已修/51未修完，前67已确认提交a92ccf9，本组待结果确认及记录提交；正式忽略产物已生效，不能将待文档commit理解为资产尚未更新，也不能将文档commit理解为镜像备份。

| 验收 | 最终事实与证据 |
|---|---|
| 旧正式资产 | 更新前108个唯一连续extent均逐字节匹配安装文件、48个ELF仅/bin/nterm不在VME域；旧build ELF/安装/盘中nterm SHA696c8f…，entry8300fc7c，两个PT_LOAD为83000000/83014000。其历史准确源码与flags Unknown，不猜测谁/何时生成。entry/before-geometry |
| 当前源码动态拒绝 | 正式nanos目录make -j4 ARCH=riscv64-nemu git_commit= run，约1.217秒，nterm init的context_uload断言受控失败，NEMU BAD TRAP、make exit2。这是当前严格loader对旧资产的预期失败见证，不是启动PASS；未回退已修loader去重演危险共享内核映射。before-run.py/log/result |
| 正式标准更新 | 同目录同参数update，exit0/38.507秒，未额外clean、未安装/下载、未人工替换ELF/盘。现有HAS_VME传VME=1、LNK_ADDR选择40000000，APP依赖phony libs，正常update会重链接/安装/重新打包；实际660条编译、16次链接，包括真实libos syscall重编，当前链无需新依赖或入口。update.py/log/result及源码身份 |
| 最终正式资产 | 108连续extent及全部48ELF文件/段/entry/页同余/用户域/栈边界通过；四启动真实build链接等于安装和盘。nterm entry40010608、两段40000000/40017000；正式files.h/syscall.h/ramdisk链接保持原目标，盘/头/内核已更新。after-geometry/current-links/formal-assets-after |
| 正式真实运行 | 正式nanos make run，使用当前正式内核/盘/NEMU，约53.451秒，8帧已目视，10实际SDL键事件；PAL标题/飞鸟、NTerm的qzx not found后prompt、NSlider0→1→0的SHA复原、回到PAL及Enter继续，hello33→144。自有组SIGTERM、make-15为观察结束，不是guest正常退出；不是人工GUI/物理音视频/长期验收。nanos/result/guest/observe及visual-qa |
| 最终检查 | 218项preclean全PASS，12项源码/配置身份保持、根/nested HEAD与index保持，nested内容干净及850原mode不变；NEMU二进制SHA不变。旧失败与新正常路径明确区分，未从旧二进制存在推定同版。validation-preclean/entry |

这次问题是正式工作树中的旧VME错配产物；当前源码的标准更新足以纠正。`HAS_VME`从当前common.h取值，update递归参数`VME=1`，RISC-V链接脚本以该参数选择40000000。`$(APP): $(OBJS) libs`中的libs是.PHONY，已有重链接不会因旧nterm build存在而跳过；安装后按当前fsimg重新生成表和盘。以上用实际无clean更新证实，不据此声称所有编译参数的失效关系均完善，亦不改写旧镜像来源Unknown。

本次生产源码diff为空，归档的源码diff/正反补丁要求不适用于这次纯产物修复；没有制造空壳代码改动。下列前后身份及ELF几何记录实际变化，旧SHA不表示仍保存旧镜像；旧产物按既有清理约定不另留副本。

## 正式产物前后身份

所有路径相对根工作区；源码基线root `a92ccf9a7a594d6d4ab024dd75bc8e5c48b2a761`、newlib nested `8101fad4376b7df0e3ec18db2db8cfa32746ad3a`，生产源码本组未改。下列新资产为`WORKTREE（2026-10-20，本地忽略构建/安装产物）`，不是Git已保存blob。

| 产物 | 旧SHA256 | 新SHA256 |
|---|---|---|
| `navy-apps/build/ramdisk.img` | `815fca56e386ad16df98941d1a7cace235cc6e92cc166cd781d7ded9d913e7d4` | `38f7a7a2bc3969b55e869e1b7a15527f6347747cfbc77982d49d5f3f58125086` |
| `navy-apps/build/ramdisk.h` | `12fc87908fff33ad974e5ceffe80a047702e30794514cf13625614de01a932a5` | `6f5dfaf09b8dbc4afa065db09f565e2995d9cbeefcca1fdaca3fe1c55bb21c98` |
| `nanos-lite/build/nanos-lite-riscv64-nemu.bin` | `1552e29931648d605e981ec24b08cdda3b271d2efe710c2b67b362dae0e86a8a` | `782ea4d956446509febebaaff620ef82de21240ded8e22b1ce030b9d17e363b7` |
| `nemu/build/riscv64-nemu-interpreter` | `bcef3bb3b53aee03b20796847461259965e809e5341ac8cd7def3dfac6b52655` | `bcef3bb3b53aee03b20796847461259965e809e5341ac8cd7def3dfac6b52655` |
| `/bin/nterm`（实际链接/安装/盘内文件） | `696c8f635fc931ad603499ed8677cfd669fe6dc755b53fc90cdeb2e3418720fb` | `fac90ceaa494b1e6c819ff7ee0dabecf044b7ffef73cdd026eee780c2b643133` |

四启动程序entry：pal `0x40046ae8`, nterm `0x40010608`, nslider `0x4000a774`, hello `0x400053dc`。全部108文件的SHA/范围及48ELF几何在before/after-geometry.json；不把48个路径均当作48个独立源码构建。

## 持久化、清理与再生

正式navy-apps/build/ramdisk.img、ramdisk.h、各实际ELF/库及nanos内核等保留在原路径，这正是本组要修复的工作资产；它们不随普通Git commit备份。现有fsimg资源/应用repo与工具需同工作区携带，entry及108项前后身份说明所用资产，不承诺仅根Git可还原全部外部资源。HEAD/配置/资源齐备时，在nanos目录按如下已有入口再生：

```sh
make -j4 ARCH=riscv64-nemu git_commit= update
make -j4 ARCH=riscv64-nemu git_commit= run
```

`git_commit=`仅关闭验证期间既有tracer自动提交，不新增产品选项。精确cwd/环境/argv/退出码在before-run-result、update-result及nanos/result。local/update.py在已固定before见证的本地恢复环境执行正式更新并准备观察器；全新冷启动不应跳过before身份记录或把未来HEAD当本组基线。等价坏地址见证可在隔离副本以现有非VME链接地址构造，不在正式盘上故意制造回退；历史696c8f…字节源Unknown，不能保证逐字节重建。

完成目视和218项检查后，仅清理本记录local的10项截图/contact/observer.so，共15,579,212逻辑字节，零tracked删除；正式更新资产完全保留。cleanup-plan/receipt记录删除前路径/字节/SHA及预期缺失，旧截图不可再直接查看；最小观察源、真实命令、结果和身份保留。local/.agent依旧本地忽略，不能以文档commit推定其已备份。

未新跑host功能测试或CPU/RT/REF：没有生产源码修改，这些消费者不使用本次正式Navy启动产物。NPC/其他ISA、完整命令集、长时/真实音视频均NotRun；不将53秒观察视作完整Linux/OS验收，也不推进M2。

整组完成后停止，等待结果确认/必要文档提交，不自动提交/新组/push。未来仅TASK_QUEUE#crp-next，不从本报告另排一份Next。可在当前对话继续：本次为短的资产闭环，下一单元仍复用exec/update→run背景；每次实际提交落档仍按AGENTS第6条重新评估会话长度与恢复可靠性。


<a id="submit-20261020"></a>
## 2026-10-20 确认与实际提交附记

用户“提交后继续”确认F0074并授权实际提交后一个单元。根实际`b2603592510d20b8cd4467128e8d936e498d143a`，5文档85增5删，实际路径/mode/blob与暂存完全一致；39保留身份/390既有检查及正式资产身份复用。提交时root工作树/index干净，nested8101fad内容/index干净且850原mode保持，未push。local/submit-precheck/staged/receipt记录实际回执；本附记及后续导航/状态变化解释原manifest文档哈希改变，不覆盖旧验收。正式忽略产物仍本地保留，文档commit不备份它们。

提交落档建议“可在当前对话继续”，依据为后续仍复用exec/update→run且恢复入口完整。本轮按用户同句明确授权执行F0087，不从commit本身授权续作或提交新结果；下一入口仍只在TASK_QUEUE#crp-next。
