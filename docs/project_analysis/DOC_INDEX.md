# 文档索引

> **更新时间**: 2026-02-26

---

## 本文件夹文档

| 文档 | 说明 |
|------|------|
| [README.md](README.md) | 文件夹说明 |
| [COMPREHENSIVE_ANALYSIS.md](COMPREHENSIVE_ANALYSIS.md) | **综合分析报告** |
| [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) | 项目整体分析 |
| [OPTIMIZATION_ROADMAP.md](OPTIMIZATION_ROADMAP.md) | 四阶段优化计划 |
| [TECH_DEBT.md](TECH_DEBT.md) | 技术债务清单 |

---

## 项目文档 (../)

### 协议规范

| 文档 | 说明 |
|------|------|
| [PROTOCOL_SPEC.md](../PROTOCOL_SPEC.md) | 完整协议规范 |
| [FEC_PLI_PROTOCOL_SPEC.md](../FEC_PLI_PROTOCOL_SPEC.md) | FEC 纠错协议 |

### 性能相关

| 文档 | 说明 |
|------|------|
| [GIL_COMPETITION_ISSUE.md](../GIL_COMPETITION_ISSUE.md) | GIL 竞争问题 |
| [PYTHON_GIL_COMPETITION_RISKS.md](../PYTHON_GIL_COMPETITION_RISKS.md) | GIL 风险防范 |

---

## 开发文档 (../development/)

### 架构文档

| 文档 | 说明 |
|------|------|
| [NETWORK_PIPELINE.md](../development/NETWORK_PIPELINE.md) | 网络管道 |
| [VIDEO_AUDIO_PIPELINE.md](../development/VIDEO_AUDIO_PIPELINE.md) | 音视频管道 |
| [NEXT_GEN_ARCHITECTURE.md](../development/NEXT_GEN_ARCHITECTURE.md) | 下一代架构 |
| [PROTOCOL_CHANGE_CHECKLIST.md](../development/PROTOCOL_CHANGE_CHECKLIST.md) | 协议修改检查清单 |

### 开发指南

| 文档 | 说明 |
|------|------|
| [DEVELOPMENT_WORKFLOW.md](../development/DEVELOPMENT_WORKFLOW.md) | 开发工作流 |
| [REFACTOR_SAFETY_GUIDE.md](../development/REFACTOR_SAFETY_GUIDE.md) | 重构安全指南 |
| [MULTIPROCESSING_BEST_PRACTICES.md](../development/MULTIPROCESSING_BEST_PRACTICES.md) | 多进程最佳实践 |

### 功能文档

| 文档 | 说明 |
|------|------|
| [MCP_FILE_TRANSFER_API.md](../development/MCP_FILE_TRANSFER_API.md) | 文件传输 API |
| [AUDIO_RECORDING_GUIDE.md](../development/AUDIO_RECORDING_GUIDE.md) | 音频录制指南 |

### 性能分析

| 文档 | 说明 |
|------|------|
| [E2E_LATENCY_ANALYSIS.md](../development/E2E_LATENCY_ANALYSIS.md) | E2E 延迟分析 |
| [CPU_OPTIMIZATION_RESEARCH.md](../development/CPU_OPTIMIZATION_RESEARCH.md) | CPU 优化研究 |

---

## 已知问题 (../development/known_issues/)

### 已修复

| 文档 | 问题 |
|------|------|
| [SCREEN_ROTATION_FIX.md](../development/known_issues/SCREEN_ROTATION_FIX.md) | 屏幕旋转 |
| [VBR_LATENCY_ISSUE.md](../development/known_issues/VBR_LATENCY_ISSUE.md) | VBR 延迟 |
| [landscape_touch_fix.md](../development/known_issues/landscape_touch_fix.md) | 横屏触摸 |
| [vbr_static_frame_stall.md](../development/known_issues/vbr_static_frame_stall.md) | VBR 静止画面 |

### 待处理

| 文档 | 问题 | 优先级 |
|------|------|--------|
| [MULTIPROCESS_DECODER_ISSUE.md](../development/known_issues/MULTIPROCESS_DECODER_ISSUE.md) | 多进程 UV 异常 | 高 |
| [iframe_interval_issue.md](../development/known_issues/iframe_interval_issue.md) | I-frame 间隔 | 中 |

### 分析报告

| 文档 | 说明 |
|------|------|
| [FRAME_SKIP_ANALYSIS.md](../development/known_issues/FRAME_SKIP_ANALYSIS.md) | Frame Skip 根因 |

---

## 按主题查找

### 我想了解...

| 主题 | 文档 |
|------|------|
| **协议和通信** | [PROTOCOL_SPEC.md](../PROTOCOL_SPEC.md) |
| **性能问题** | [GIL_COMPETITION_ISSUE.md](../GIL_COMPETITION_ISSUE.md) |
| **帧丢失问题** | [FRAME_SKIP_ANALYSIS.md](../development/known_issues/FRAME_SKIP_ANALYSIS.md) |
| **文件传输** | [MCP_FILE_TRANSFER_API.md](../development/MCP_FILE_TRANSFER_API.md) |
| **音频录制** | [AUDIO_RECORDING_GUIDE.md](../development/AUDIO_RECORDING_GUIDE.md) |
| **多进程开发** | [MULTIPROCESSING_BEST_PRACTICES.md](../development/MULTIPROCESSING_BEST_PRACTICES.md) |
| **修改协议** | [PROTOCOL_CHANGE_CHECKLIST.md](../development/PROTOCOL_CHANGE_CHECKLIST.md) |

---

*此索引由文档系统生成*
