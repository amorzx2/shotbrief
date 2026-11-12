# ShotBrief

A small, offline Python tool that validates JSON shot lists and exports Markdown prompt cards for AI video planning.

一个离线分镜小工具：检查 JSON 分镜表，并导出适合复制与修改的 Markdown 视频提示词卡片。

**Status:** initial version, 0.1.0. This is a new project, not an established or widely adopted tool. AI-assisted implementation. No claimed usage statistics or model integrations.

**状态：** 初始版本。没有历史用户量或成熟度承诺。本项目不生成视频，不调用模型，也不自动优化提示词。

## Run / 使用

Requires Python 3.9+; standard library only, no install or API key needed. Run commands in the repository folder.

需要 Python 3.9 或以上版本，无第三方依赖、无 API 密钥。在项目目录运行：

```sh
python shotbrief.py examples/shotlist.json --check
python shotbrief.py examples/shotlist.json -o prompts.md
python shotbrief.py examples/shotlist.json
python -m unittest discover -s tests -v
```

On some systems use `python3` instead of `python`. On Windows, `py -3` also works. If redirecting Chinese output in an older terminal, use `-o` for a UTF-8 file instead.

Existing output files are protected. Add `--force` only when you intend to replace them. Input and output cannot be the same path. `--check` validates without creating output. Files are handled locally; no telemetry or network requests.

默认不会覆盖现有文件；确认替换时再加 `--force`。输入文件不能作为输出文件。所有处理均在本地完成，不上传、不联网。

## Input / 输入格式

```json
{
  "title": "Morning",
  "shots": [
    {
      "duration": 6,
      "scene": "A sunlit room",
      "camera": "A slow forward movement",
      "action": "A curtain lifts in the breeze",
      "ending": "The white curtain fills the frame"
    }
  ]
}
```

All fields are required. `duration` is a finite number of seconds greater than zero and at most 86400 (one day). Text fields must contain non-whitespace text; Chinese and English can be mixed. Unknown fields and duplicate JSON keys are rejected to catch typos. Shot numbers in errors are one-based. Duration is descriptive metadata, not a guarantee that a video model supports it.

所有字段均必填。`duration` 是大于零、最大为 86400（一日）的有限秒数；其余字段为非空文字，支持中英混合。未知字段和重复键会报错。报错中的分镜编号从 1 开始。时长只是策划信息，不保证模型支持该时长。

## Output and limits / 输出与限制

Each shot becomes a numbered card with duration, scene, camera, action, ending, and a single combined prompt. The tool preserves your intent instead of inventing content. Markdown/HTML characters in your text are escaped for display. Read and adapt the result before using it with a video model; this tool cannot verify artistic quality, factual accuracy, continuity, licensing, or provider compatibility.

每镜头导出一张分镜卡片和合并提示词，不凭空补写内容。文本中的 Markdown/HTML 字符会转义。使用前请自行检查效果、连续性、素材权限和模型限制。

## Contributing / 贡献

Bug reports should include a minimal, non-sensitive JSON example, the command, Python version, and expected result. Please do not upload private client briefs, personal information, credentials, or copyrighted source assets. Keep additions small and include tests.

反馈问题时请提供不含敏感信息的最小示例、命令、Python 版本及预期结果。请勿上传客户私密需求、个人信息、密钥或无权公开的素材。

MIT licensed. See [LICENSE](LICENSE).
