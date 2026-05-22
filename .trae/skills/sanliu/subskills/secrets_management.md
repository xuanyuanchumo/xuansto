# 密钥与环境变量管理系统 (Secrets Management)

## 概述

密钥与环境变量管理系统是 Sanliu v4.0 的安全基础设施，提供统一的密钥管理、硬编码检测、配置安全审计和环境变量模板生成能力。该系统通过多源加载链、智能分类、日志脱敏和强度验证等机制，确保项目中的敏感信息得到妥善保护。

### 核心理念

- **统一管理**: 集中管理所有类型的密钥和环境变量
- **多源加载**: 支持从多个来源加载密钥，优先级明确
- **类型安全**: 自动识别密钥类型，提供类型安全的访问接口
- **日志脱敏**: 自动对日志中的敏感信息进行脱敏处理
- **硬编码检测**: 扫描代码中的硬编码敏感信息
- **配置审计**: 审计配置文件的安全性和合规性

### 系统组成

```
┌─────────────────────────────────────────────────────────────────┐
│              密钥与环境变量管理系统架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           SecretsManager (密钥管理器)                      │  │
│  │  ├─ 多源加载链 (.env → .env.local → os.environ → defaults)│  │
│  │  ├─ 8种密钥类型分类                                        │  │
│  │  ├─ 类型安全访问 (get/get_required)                       │  │
│  │  ├─ 日志脱敏 (mask_for_log)                               │  │
│  │  └─ 强度验证 (validate_all)                               │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         HardcodedDetector (硬编码检测器)                   │  │
│  │  ├─ 25种正则模式检测                                      │  │
│  │  ├─ SARIF v2.1.0 导出                                    │  │
│  │  └─ Markdown 报告生成                                    │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │      ConfigSecurityAuditor (配置安全审计器)                │  │
│  │  ├─ YAML/JSON 敏感字段检测                                │  │
│  │  ├─ 文件权限检查                                         │  │
│  │  ├─ .gitignore 合规检查                                  │  │
│  │  └─ 加密存储评估                                         │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │       EnvTemplateGenerator (环境变量模板生成器)            │  │
│  │  ├─ os.environ 使用扫描                                   │  │
│  │  ├─ .env.example 生成                                     │  │
│  │  └─ Markdown 参考文档生成                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## SecretsManager (密钥管理器)

### 功能概述

SecretsManager是核心的密钥管理组件，负责密钥的加载、存储、访问和安全处理。

### 支持的密钥类型

```python
class SecretType(Enum):
    """密钥类型"""
    PASSWORD = "password"                    # 密码
    API_KEY = "api_key"                      # API密钥
    TOKEN = "token"                          # 令牌
    SECRET = "secret"                        # 密钥
    CREDENTIAL = "credential"                # 凭证
    CONNECTION_STRING = "connection_string"  # 连接字符串
    PRIVATE_KEY = "private_key"              # 私钥
    ENCRYPTION_KEY = "encryption_key"        # 加密密钥
```

### 多源加载链

SecretsManager支持从多个来源加载密钥，按以下优先级顺序（高→低）：

```
1. .env.local          ← 最高优先级（本地开发覆盖）
2. .env                 ← 项目默认配置
3. os.environ          ← 系统环境变量
4. defaults            ← 默认值（最低优先级）
```

**实现方式**:
```python
class SecretsManager:
    def load(self, env_file: str = '.env', env_local_file: str = '.env.local'):
        """
        从多个来源加载密钥

        Args:
            env_file: 主环境文件路径
            env_local_file: 本地环境文件路径
        """
        self._secrets = {}

        # 1. 加载默认值
        self._load_defaults()

        # 2. 加载系统环境变量
        self._load_os_environ()

        # 3. 加载.env文件
        if os.path.exists(env_file):
            self._load_env_file(env_file)

        # 4. 加载.env.local文件（最高优先级）
        if os.path.exists(env_local_file):
            self._load_env_file(env_local_file)

        # 5. 自动分类所有密钥
        self._classify_all_secrets()

    def _load_env_file(self, file_path: str):
        """加载环境文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                self._secrets[key] = {
                    'value': value,
                    'source': file_path,
                    'type': None  # 稍后自动分类
                }
```

### 核心API接口

#### get() 方法

```python
class SecretsManager:
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取密钥值（带默认值）

        Args:
            key: 密钥键名
            default: 默认值（如果密钥不存在）

        Returns:
            Any: 密钥值或默认值
        """
        if key in self._secrets:
            return self._secrets[key]['value']
        return default
```

#### get_required() 方法

```python
class SecretsManager:
    def get_required(self, key: str) -> Any:
        """
        获取必需的密钥值（不存在时抛出异常）

        Args:
            key: 密钥键名

        Returns:
            Any: 密钥值

        Raises:
            SecretNotFoundError: 密钥不存在
        """
        if key not in self._secrets:
            raise SecretNotFoundError(key)
        return self._secrets[key]['value']
```

#### classify() 方法

```python
class SecretsManager:
    def classify(self, key: str) -> SecretType:
        """
        分类密钥类型

        Args:
            key: 密钥键名

        Returns:
            SecretType: 密钥类型
        """
        if key in self._secrets and self._secrets[key].get('type'):
            return self._secrets[key]['type']

        # 基于键名的模式匹配
        type_patterns = {
            SecretType.PASSWORD: [
                r'password', r'passwd', r'pwd', r'密码'
            ],
            SecretType.API_KEY: [
                r'api[_-]?key', r'apikey', r'api[_-]?secret',
                r'access[_-]?key'
            ],
            SecretType.TOKEN: [
                r'token', r'auth[_-]?token', r'access[_-]?token',
                r'refresh[_-]?token', r'jwt', r'令牌'
            ],
            SecretType.SECRET: [
                r'secret', r'client[_-]?secret',
                r'webhook[_-]?secret'
            ],
            SecretType.CREDENTIAL: [
                r'credential', r'creds', r'auth', r'凭证'
            ],
            SecretType.CONNECTION_STRING: [
                r'connection[_-]?string', r'database[_-]?url',
                r'mongodb', r'redis[_-]?url', r'postgres',
                r'mysql', r'连接字符串'
            ],
            SecretType.PRIVATE_KEY: [
                r'private[_-]?key', r'pem', r'.p12$', r'.pfx$',
                r'私钥'
            ],
            SecretType.ENCRYPTION_KEY: [
                r'encrypt', r'decrypt', r'aes[_-]?key',
                r'cipher', r'加密'
            ]
        }

        key_lower = key.lower()
        for secret_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, key_lower):
                    if key in self._secrets:
                        self._secrets[key]['type'] = secret_type
                    return secret_type

        # 默认为SECRET类型
        if key in self._secrets:
            self._secrets[key]['type'] = SecretType.SECRET
        return SecretType.SECRET
```

#### mask_for_log() 方法

```python
class SecretsManager:
    def mask_for_log(self, value: str, keep_chars: int = 2) -> str:
        """
        对值进行日志脱敏

        Args:
            value: 原始值
            keep_chars: 首尾保留的字符数

        Returns:
            str: 脱敏后的值
        """
        if not value or len(value) <= keep_chars * 2:
            return '*' * len(value) if value else ''

        masked = (
            value[:keep_chars] +
            '*' * (len(value) - keep_chars * 2) +
            value[-keep_chars:]
        )
        return masked
```

#### validate_all() 方法

```python
class SecretsManager:
    def validate_all(self) -> Dict[str, ValidationResult]:
        """
        验证所有密钥强度

        Returns:
            Dict[str, ValidationResult]: 每个密钥的验证结果
        """
        results = {}

        for key, info in self._secrets.items():
            value = info['value']
            secret_type = info.get('type', self.classify(key))

            validation = ValidationResult(
                key=key,
                is_valid=True,
                issues=[]
            )

            # 基本长度检查
            if len(value) < 8:
                validation.is_valid = False
                validation.issues.append(f"密钥长度过短 ({len(value)} < 8)")

            # 类型特定验证
            if secret_type == SecretType.PASSWORD:
                if not re.search(r'[A-Z]', value):
                    validation.is_valid = False
                    validation.issues.append("缺少大写字母")
                if not re.search(r'[a-z]', value):
                    validation.is_valid = False
                    validation.issues.append("缺少小写字母")
                if not re.search(r'\d', value):
                    validation.is_valid = False
                    validation.issues.append("缺少数字")
                if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
                    validation.is_valid = False
                    validation.issues.append("缺少特殊字符")

            elif secret_type == SecretType.API_KEY:
                if len(value) < 16:
                    validation.is_valid = False
                    validation.issues.append(f"API密钥过短 ({len(value)} < 16)")

            elif secret_type == SecretType.TOKEN:
                if '.' not in value and len(value) < 20:
                    validation.is_valid = False
                    validation.issues.append("Token格式可能不正确")

            results[key] = validation

        return results
```

### 配置参数

```yaml
secrets_manager:
  # 环境文件配置
  env_files:
    primary: ".env"
    local: ".env.local"

  # 脱敏配置
  masking:
    enabled: true
    keep_first_chars: 2
    keep_last_chars: 2
    mask_char: "*"

  # 验证配置
  validation:
    min_password_length: 8
    require_uppercase: true
    require_lowercase: true
    require_digit: true
    require_special_char: true
    min_api_key_length: 16
```

## HardcodedDetector (硬编码检测器)

### 功能概述

HardcodedDetector用于扫描源代码中的硬编码敏感信息，防止密钥泄露到代码仓库中。

### 支持的检测模式 (25种正则模式)

#### 密码相关 (10个)

| ID | 模式 | 说明 | 严重程度 |
|----|------|------|---------|
| HW-001 | `password\s*=\s*["'][^"']+["']` | 硬编码密码 | CRITICAL |
| HW-002 | `passwd\s*=\s*["'][^"']+["']` | passwd赋值 | CRITICAL |
| HW-003 | `pwd\s*=\s*["'][^"']+["']` | pwd赋值 | CRITICAL |
| HW-004 | `"password"\s*:\s*"[^"]+"` | JSON密码字段 | CRITICAL |
| HW-005 | `'password'\s*:\s*'[^']+'` | Python字典密码 | CRITICAL |
| HW-006 | `--password\s+\w+` | CLI密码参数 | HIGH |
| HW-007 | `-p\s+["']?\w+["']?` | 短密码参数 | HIGH |
| HW-008 | `PASSWORD\s*=\s*\w{4,}` | 环境变量风格密码 | CRITICAL |
| HW-009 | `DB_PASSWORD\s*=\s*[^#\n]+` | 数据库密码 | CRITICAL |
| HW-010 | `admin_password\s*=\s*[^#\n]+` | 管理员密码 | CRITICAL |

#### API密钥/Token (10个)

| ID | 模式 | 说明 | 严重程度 |
|----|------|------|---------|
| HW-011 | `api[_-]?key\s*=\s*["'][A-Za-z0-9]{20,}["']` | API密钥 | CRITICAL |
| HW-012 | `apikey\s*=\s*["'][A-Za-z0-9]{20,}["']` | apikey格式 | CRITICAL |
| HW-013 | `token\s*=\s*["'][A-Za-z0-9._-]{20,}["']` | Token | CRITICAL |
| HW-014 | `secret[_-]?key\s*=\s*["'][A-Za-z0-9+/=]{20,}["']` | 秘钥 | CRITICAL |
| HW-015 | `AKIA[0-9A-Z]{16}` | AWS Access Key | CRITICAL |
| HW-016 | `ghp_[A-Za-z0-9_]{36}` | GitHub PAT | CRITICAL |
| HW-017 | `xox[bpsa]-[A-Za-z0-9-]+` | Slack Token | HIGH |
| HW-018 | `sk-[A-Za-z0-9]{32,}` | OpenAI Key | CRITICAL |
| HW-019 | `AIza[A-Za-z0-9_-]{35}` | Google API Key | CRITICAL |
| HW-020 | `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` | JWT Token | HIGH |

#### 连接字符串/云密钥 (5个)

| ID | 模式 | 说明 | 严重程度 |
|----|------|------|---------|
| HW-021 | `mongodb\+?://\w+:\w+@` | MongoDB连接串 | CRITICAL |
| HW-022 | `postgres(?:ql)?://\w+:\w+@` | PostgreSQL连接串 | CRITICAL |
| HW-023 | `mysql://\w+:\w+@` | MySQL连接串 | CRITICAL |
| HW-024 | `redis://:\w+@` | Redis连接串 | HIGH |
| HW-025 | `AccountKey=[A-Za-z0-9+/=]{44}` | Azure Storage Key | CRITICAL |

### 核心API接口

#### scan_directory() 方法

```python
class HardcodedDetector:
    def scan_directory(self, path: Path, exclude_dirs: List[str] = None) -> DetectionReport:
        """
        扫描目录中的硬编码信息

        Args:
            path: 要扫描的目录路径
            exclude_dirs: 排除的目录列表

        Returns:
            DetectionReport: 检测报告
        """
        report = DetectionReport(
            scan_path=str(path),
            scanned_at=datetime.now(),
            detections=[]
        )

        # 默认排除目录
        default_excludes = [
            'node_modules', '__pycache__', '.git', 'venv',
            '.venv', 'dist', 'build', '.next', '.cache'
        ]
        exclude_dirs = exclude_dirs or default_excludes

        # 支持的文件扩展名
        supported_extensions = [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go',
            '.rb', '.php', '.c', '.cpp', '.h', '.cs', '.swift',
            '.kt', '.rs', '.scala', '.vue', '.svelte', '.yaml',
            '.yml', '.json', '.xml', '.ini', '.cfg', '.conf',
            '.env', '.sh', '.bash', '.ps1', '.sql', '.html',
            '.css', '.scss', '.less', '.md', '.txt'
        ]

        # 递归扫描文件
        for root, dirs, files in os.walk(path):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                file_path = Path(root) / file
                if file_path.suffix.lower() in supported_extensions:
                    file_detections = self.scan_file(file_path)
                    report.detections.extend(file_detections)

        # 统计
        report.total_files_scanned = sum(1 for _, _, _ in ...)
        report.total_detections = len(report.detections)
        report.critical_count = sum(1 for d in report.detections if d.severity == Severity.CRITICAL)
        report.high_count = sum(1 for d in report.detections if d.severity == Severity.HIGH)
        report.medium_count = sum(1 for d in report.detections if d.severity == Severity.MEDIUM)
        report.low_count = sum(1 for d in report.detections if d.severity == Severity.LOW)

        return report
```

#### export_report_sarif() 方法

```python
class HardcodedDetector:
    def export_report_sarif(self, report: DetectionReport, output_path: str):
        """
        导出SARIF v2.1.0格式报告

        Args:
            report: 检测报告
            output_path: 输出文件路径
        """
        sarif_report = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "Sanliu HardcodedDetector",
                        "version": "4.0.0",
                        "rules": {}
                    }
                },
                "results": []
            }]
        }

        # 构建规则和结果
        rule_index = 0
        rules_dict = sarif_report["runs"][0]["tool"]["driver"]["rules"]

        for detection in report.detections:
            pattern_id = detection.pattern_id

            # 添加规则（如果不存在）
            if pattern_id not in rules_dict:
                rules_dict[pattern_id] = {
                    "id": pattern_id,
                    "name": detection.pattern_name,
                    "shortDescription": {"text": detection.description},
                    "properties": {
                        "severity": detection.severity.value,
                        "category": detection.category
                    },
                    "helpUri": f"https://sanliu.dev/security/hardcoded/{pattern_id}"
                }

            # 添加结果
            result = {
                "ruleId": pattern_id,
                "level": "error" if detection.severity == Severity.CRITICAL else
                       "warning" if detection.severity == Severity.HIGH else
                       "note",
                "message": {"text": detection.description},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": detection.file_path},
                        "region": {
                            "startLine": detection.line_number,
                            "startColumn": detection.column_number,
                            "endLine": detection.line_number,
                            "endColumn": detection.column_number + len(detection.matched_text)
                        }
                    }
                }],
                "properties": {
                    "matchedText": detection.matched_text,
                    "patternId": pattern_id
                }
            }

            sarif_report["runs"][0]["results"].append(result)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sarif_report, f, indent=2, ensure_ascii=False)
```

#### export_report_markdown() 方法

```python
class HardcodedDetector:
    def export_report_markdown(self, report: DetectionReport, output_path: str):
        """
        导出Markdown格式报告

        Args:
            report: 检测报告
            output_path: 输出文件路径
        """
        lines = []

        lines.append("# 硬编码敏感信息检测报告")
        lines.append("")
        lines.append(f"**扫描时间**: {report.scanned_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**扫描路径**: {report.scan_path}")
        lines.append(f"**扫描文件数**: {report.total_files_scanned}")
        lines.append("")

        # 统计摘要
        lines.append("## 检测统计")
        lines.append("")
        lines.append("| 严重程度 | 数量 |")
        lines.append("|---------|-----|")
        lines.append(f"| 🔴 CRITICAL | {report.critical_count} |")
        lines.append(f"| 🟠 HIGH | {report.high_count} |")
        lines.append(f"| 🟡 MEDIUM | {report.medium_count} |")
        lines.append(f"| 🟢 LOW | {report.low_count} |")
        lines.append(f"| **总计** | **{report.total_detections}** |")
        lines.append("")

        # 详细检测结果
        lines.append("## 检测详情")
        lines.append("")

        # 按严重程度分组
        severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
        for severity in severity_order:
            detections = [d for d in report.detections if d.severity == severity]
            if not detections:
                continue

            severity_icon = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}
            lines.append(f"### {severity_icon[severity.value]} {severity.value}")
            lines.append("")

            for i, det in enumerate(detections, 1):
                lines.append(f"#### {i}. [{det.pattern_id}] {det.pattern_name}")
                lines.append("")
                lines.append(f"- **文件**: `{det.file_path}:{det.line_number}`")
                lines.append(f"- **内容**: `{det.matched_text[:50]}...`" if len(det.matched_text) > 50 else f"- **内容**: `{det.matched_text}`")
                lines.append(f"- **类别**: {det.category}")
                lines.append(f"- **建议**: {det.remediation}")
                lines.append("")

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
```

### 配置参数

```yaml
hardcoded_detector:
  # 扫描配置
  scanning:
    supported_extensions:
      - ".py"
      - ".js"
      - ".ts"
      - ".tsx"
      - ".jsx"
      - ".go"
      - ".rs"
      - ".java"
      - ".yaml"
      - ".yml"
      - ".json"
      - ".env"
      - ".md"
    exclude_dirs:
      - "node_modules"
      - "__pycache__"
      - ".git"
      - "venv"
      - ".venv"
      - "dist"
      - "build"
      - ".cache"

  # 报告配置
  reporting:
    output_formats:
      - "sarif"
      - "markdown"
    output_dir: "reports/security"
    include_source_context: true
    context_lines: 3
```

## ConfigSecurityAuditor (配置安全审计器)

### 功能概述

ConfigSecurityAuditor用于审计配置文件的安全性，包括敏感字段检测、权限检查、.gitignore合规性验证等。

### 审计功能

#### 1. 敏感字段检测

```python
class ConfigSecurityAuditor:
    SENSITIVE_FIELD_PATTERNS = [
        (r'(?:password|passwd|pwd)\s*[:=]', 'CRITICAL', '密码字段'),
        (r'(?:api[_-]?key|apikey)\s*[:=]', 'CRITICAL', 'API密钥'),
        (r'(?:secret|token)\s*[:=]', 'HIGH', '密钥/令牌'),
        (r'(?:credential|auth)\s*[:=]', 'HIGH', '凭证'),
        (r'(?:connection[_-]?string|database[_-]?url)\s*[:=]', 'CRITICAL', '连接字符串'),
        (r'(?:private[_-]?key)\s*[:=]', 'CRITICAL', '私钥'),
        (r'(?:encryption[_-]?key)\s*[:=]', 'CRITICAL', '加密密钥'),
        (r'(?:access[_-]?key)\s*[:=]', 'CRITICAL', '访问密钥'),
        (r'(?:webhook[_-]?secret)\s*[:=]', 'HIGH', 'Webhook密钥'),
        (r'(?:ssh[_-]?key)\s*[:=]', 'CRITICAL', 'SSH密钥'),
        (r'(?:certificate)\s*[:=]', 'MEDIUM', '证书'),
        (r'(?:license[_-]?key)\s*[:=]', 'MEDIUM', '许可证密钥'),
        (r'(?:stripe|paypal|alipay)', 'HIGH', '支付相关'),
        (r'(?:aws_access_key|aws_secret_key)', 'CRITICAL', 'AWS凭证'),
        (r'(?:sendgrid|mailgun|twilio)', 'HIGH', '第三方服务密钥'),
        (r'(?:redis|mongo|postgres|mysql)\s*(?:url|host)\s*[:=]', 'HIGH', '数据库配置'),
        (r'(?:jwt|bearer)\s*[:=]', 'HIGH', 'JWT/Bearer令牌')
    ]

    def audit_config_file(self, file_path: Path) -> ConfigAuditResult:
        """
        审计配置文件

        Args:
            file_path: 配置文件路径

        Returns:
            ConfigAuditResult: 审计结果
        """
        result = ConfigAuditResult(file_path=str(file_path))

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检测敏感字段
        for pattern, severity, description in self.SENSITIVE_FIELD_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                result.findings.append(AuditFinding(
                    type='sensitive_field',
                    severity=severity,
                    line_number=content[:match.start()].count('\n') + 1,
                    matched_text=match.group(),
                    description=f"发现敏感字段: {description}"
                ))

        # 统计
        result.critical_count = sum(1 for f in result.findings if f.severity == 'CRITICAL')
        result.high_count = sum(1 for f in result.findings if f.severity == 'HIGH')

        result.is_secure = result.critical_count == 0 and result.high_count == 0

        return result
```

#### 2. 文件权限检查

```python
class ConfigSecurityAuditor:
    def check_file_permissions(self, file_path: Path) -> PermissionCheckResult:
        """
        检查文件权限

        Args:
            file_path: 文件路径

        Returns:
            PermissionCheckResult: 权限检查结果
        """
        result = PermissionCheckResult(file_path=str(file_path))

        if not file_path.exists():
            result.is_valid = False
            result.issues.append("文件不存在")
            return result

        # 获取文件权限
        stat_info = file_path.stat()

        # 检查是否可被其他用户读取
        mode = stat_info.st_mode
        world_readable = bool(mode & stat.S_IROTH)
        world_writable = bool(mode & stat.S_IWOTH)

        if world_readable:
            result.is_valid = False
            result.issues.append(f"文件可被其他用户读取 (权限: {oct(mode)})")

        if world_writable:
            result.is_valid = False
            result.issues.append(f"文件可被其他用户写入 (权限: {oct(mode)})")

        # 对于敏感文件，要求更严格
        sensitive_names = ['.env', '.env.local', 'credentials', 'secrets', 'config']
        if any(name in file_path.name.lower() for name in sensitive_names):
            group_readable = bool(mode & stat.S_IRGRP)
            if group_readable:
                result.is_valid = False
                result.issues.append(f"敏感文件可被同组用户读取 (权限: {oct(mode)})")

        return result
```

#### 3. .gitignore合规检查

```python
class ConfigSecurityAuditor:
    SENSITIVE_FILE_PATTERNS = [
        ('.env', '环境变量文件'),
        ('.env.local', '本地环境变量文件'),
        ('.env.production', '生产环境变量文件'),
        ('credentials.*', '凭证文件'),
        ('*.pem', 'PEM证书文件'),
        ('*.p12', 'P12证书文件'),
        ('*.pfx', 'PFX证书文件'),
        ('*.key', '密钥文件'),
        ('id_rsa', 'RSA私钥'),
        ('id_ed25519', 'Ed25519私钥'),
        ('secrets.yaml', 'YAML密钥文件')
    ]

    def validate_gitignore(self, gitignore_path: Path = None) -> GitIgnoreValidationResult:
        """
        验证.gitignore是否包含必要的忽略规则

        Args:
            gitignore_path: .gitignore文件路径

        Returns:
            GitIgnoreValidationResult: 验证结果
        """
        gitignore_path = gitignore_path or Path('.gitignore')
        result = GitIgnoreValidationResult(gitignore_path=str(gitignore_path))

        if not gitignore_path.exists():
            result.is_valid = False
            result.missing_rules.extend([pattern for pattern, _ in self.SENSITIVE_FILE_PATTERNS])
            return result

        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read().lower()

        for pattern, description in self.SENSITIVE_FILE_PATTERNS:
            if pattern.lower() not in gitignore_content:
                result.missing_rules.append((pattern, description))

        result.is_valid = len(result.missing_rules) == 0

        return result
```

## EnvTemplateGenerator (环境变量模板生成器)

### 功能概述

EnvTemplateGenerator通过扫描源代码中os.environ的使用情况，自动生成.env.example文件和参考文档。

### 核心功能

#### 1. 扫描os.environ使用

```python
class EnvTemplateGenerator:
    ENVIRON_PATTERNS = [
        (r"os\.environ\.get\(['\"]([^'\"]+)['\"]", "get"),
        (r"os\.environ\[['\"]([^'\"]+)['\"]\]", "direct"),
        (r"os\.getenv\(['\"]([^'\"]+)['\"]", "getenv"),
        (r"environ\.get\(['\"]([^'\"]+)['\"]", "environ_get"),
        (r"ENV\.get\(['\"]([^'\"]+)['\"]", "django_env_get"),
        (r"app\.config\[['\"]([^'\"]+)['\"]\]", "flask_config"),
        (r"settings\.get\(['\"]([^'\"]+)['\"]", "settings_get")
    ]

    def scan_project(self, project_path: Path) -> EnvScanResult:
        """
        扫描项目中环境变量的使用情况

        Args:
            project_path: 项目根目录

        Returns:
            EnvScanResult: 扫描结果
        """
        result = EnvScanResult(project_path=str(project_path))
        env_vars = {}

        # 扫描Python文件
        for py_file in project_path.rglob('*.py'):
            if any(part.startswith('.') or part in ['node_modules', '__pycache__', 'venv', '.venv']
                   for part in py_file.parts):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern, method in self.ENVIRON_PATTERNS:
                matches = re.finditer(pattern, content)
                for match in matches:
                    var_name = match.group(1)
                    if var_name not in env_vars:
                        env_vars[var_name] = {
                            'name': var_name,
                            'method': method,
                            'files': [str(py_file)],
                            'category': self._classify_var(var_name),
                            'required': True
                        }
                    else:
                        if str(py_file) not in env_vars[var_name]['files']:
                            env_vars[var_name]['files'].append(str(py_file))

        result.environment_variables = list(env_vars.values())
        result.total_vars = len(result.environment_variables)

        return result
```

#### 2. 生成.env.example

```python
class EnvTemplateGenerator:
    def generate_example(self, scan_result: EnvScanResult, output_path: str = '.env.example'):
        """
        生成.env.example文件

        Args:
            scan_result: 扫描结果
            output_path: 输出文件路径
        """
        lines = ['# ============================================']
        lines.append('# Environment Variables Template')
        lines.append('# Generated by Sanliu v4.0 EnvTemplateGenerator')
        lines.append(f'# Generated at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        lines.append('# ============================================')
        lines.append('')
        lines.append('# Required Variables (must be set)')
        lines.append('# ----------------------------------------')

        required_vars = [v for v in scan_result.environment_variables if v['required']]
        optional_vars = [v for v in scan_result.environment_variables if not v['required']]
        secret_vars = [v for v in scan_result.environment_variables if v['category'] == 'SECRET']

        for var in required_vars:
            if var in secret_vars:
                continue
            lines.append(f"{var['name']}=")
            lines.append(f"# Used in: {', '.join(os.path.basename(f) for f in var['files'][:3])}")
            lines.append('')

        lines.append('')
        lines.append('# Optional Variables')
        lines.append('# ----------------------------------------')

        for var in optional_vars:
            if var in secret_vars:
                continue
            lines.append(f"# {var['name']}=")
            lines.append(f"# Used in: {', '.join(os.path.basename(f) for f in var['files'][:3])}")
            lines.append('')

        lines.append('')
        lines.append('# Sensitive Variables (DO NOT commit to version control)')
        lines.append('# ----------------------------------------')

        for var in secret_vars:
            lines.append(f"# {var['name']}=<your_{var['name'].lower()}_here>")
            lines.append(f"# Type: {var['category']}")
            lines.append('')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
```

#### 3. 生成参考文档

```python
class EnvTemplateGenerator:
    def generate_documentation(self, scan_result: EnvScanResult, output_path: str = 'docs/env_variables.md'):
        """
        生成环境变量参考文档

        Args:
            scan_result: 扫描结果
            output_path: 输出文件路径
        """
        lines = []
        lines.append('# Environment Variables Reference')
        lines.append('')
        lines.append('| Variable Name | Category | Required | Usage | Files |')
        lines.append('|--------------|----------|----------|-------|-------|')

        for var in sorted(scan_result.environment_variables, key=lambda x: x['name']):
            category = var['category']
            required = '✅ Yes' if var['required'] else '❌ No'
            usage = var['method']
            files = ', '.join(os.path.basename(f) for f in var['files'][:3])
            if len(var['files']) > 3:
                files += f' (+{len(var["files"]) - 3})'

            lines.append(f"| `{var['name']}` | {category} | {required} | {usage} | {files} |")

        lines.append('')
        lines.append(f'**Total: {scan_result.total_vars} variables**')
        lines.append('')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
```

## 使用示例

### 示例1: 基本密钥使用

```python
from secrets_manager import SecretsManager

# 初始化并加载密钥
sm = SecretsManager()
sm.load()

# 安全获取密钥
db_host = sm.get('DB_HOST', 'localhost')
db_port = sm.get('DB_PORT', 5432)
db_user = sm.get_required('DB_USER')
db_pass = sm.get_required('DB_PASSWORD')

print(f"数据库连接: {db_user}@{db_host}:{db_port}")

# 日志脱敏
logger.info(f"使用数据库密码: {sm.mask_for_log(db_pass)}")
# 输出: 使用数据库密码: ad**************rd
```

### 示例2: 硬编码检测

```python
from security.hardcoded_detector import HardcodedDetector

detector = HardcodedDetector()

# 扫描项目
report = detector.scan_directory(Path('.'))

print(f"扫描完成:")
print(f"  文件数: {report.total_files_scanned}")
print(f"  检测总数: {report.total_detections}")
print(f"  CRITICAL: {report.critical_count}")
print(f"  HIGH: {report.high_count}")

# 导出报告
detector.export_report_sarif(report, 'reports/security/hardcoded.sarif')
detector.export_report_markdown(report, 'reports/security/hardcoded.md')

# 检查是否有严重问题
if report.critical_count > 0:
    print("❌ 发现严重问题！请立即修复")
else:
    print("✅ 未发现严重问题")
```

### 示例3: 配置安全审计

```python
from security.config_security_auditor import ConfigSecurityAuditor

auditor = ConfigSecurityAuditor()

# 审计配置文件
result = auditor.audit_config_file(Path('config/settings.yaml'))

print(f"配置审计结果:")
print(f"  是否安全: {'是' if result.is_secure else '否'}")
print(f"  CRITICAL: {result.critical_count}")
print(f"  HIGH: {result.high_count}")

for finding in result.findings:
    print(f"  ⚠️  Line {finding.line_number}: {finding.description}")

# 检查.gitignore
gitignore_result = auditor.validate_gitignore()
if not gitignore_result.is_valid:
    print("\n.gitignore 缺少以下规则:")
    for pattern, desc in gitignore_result.missing_rules:
        print(f"  - {pattern} ({desc})")
```

### 示例4: 环境变量模板生成

```python
from security.env_template_generator import EnvTemplateGenerator

generator = EnvTemplateGenerator()

# 扫描项目
scan_result = generator.scan_project(Path('.'))

print(f"发现 {scan_result.total_vars} 个环境变量")

# 生成.env.example
generator.generate_example(scan_result, '.env.example')
print("已生成 .env.example")

# 生成参考文档
generator.generate_documentation(scan_result, 'docs/env_variables.md')
print("已生成 docs/env_variables.md")
```

### 示例5: 密钥强度验证

```python
from secrets_manager import SecretsManager

sm = SecretsManager()
sm.load()

# 验证所有密钥
results = sm.validate_all()

print("密钥强度验证结果:")
valid_count = 0
invalid_count = 0

for key, result in results.items():
    if result.is_valid:
        valid_count += 1
    else:
        invalid_count += 1
        print(f"❌ {key}:")
        for issue in result.issues:
            print(f"   - {issue}")

print(f"\n总计: {valid_count} 有效, {invalid_count} 无效")
```

## 最佳实践

### 1. 始终使用SecretsManager访问密钥

不要直接使用 `os.environ.get()` 或硬编码密钥，始终通过SecretsManager访问。

```python
# 推荐
from secrets_manager import SecretsManager
sm = SecretsManager()
sm.load()
api_key = sm.get_required('API_KEY')

# 不推荐
import os
api_key = os.environ.get('API_KEY')  # 无脱敏、无验证
# 更不推荐
api_key = 'sk-abc123...'  # 硬编码！
```

### 2. 在CI/CD中运行硬编码检测

将硬编码检测集成到CI/CD流程中，确保每次提交都经过安全检查。

```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  hardcoded-detection:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run HardcodedDetector
        run: |
          python -c "
          from security.hardcoded_detector import HardcodedDetector
          from pathlib import Path
          detector = HardcodedDetector()
          report = detector.scan_directory(Path('.'))
          detector.export_report_sarif(report, 'hardcoded.sarif')
          if report.critical_count > 0:
              exit(1)
          "

      - name: Upload SARIF Report
        if: always()
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: hardcoded.sarif
```

### 3. 定期更新.env.example

当添加新的环境变量时，及时更新.env.example文件。

```python
# 在开发新功能后运行
from security.env_template_generator import EnvTemplateGenerator

generator = EnvTemplateGenerator()
scan_result = generator.scan_project(Path('.'))
generator.generate_example(scan_result, '.env.example')
```

### 4. 使用不同的环境文件

为不同环境使用不同的环境文件：

```
.env                  # 默认配置（提交到版本控制）
.env.local            # 本地开发覆盖（不提交）
.env.staging          # 预发布环境（不提交）
.env.production       # 生产环境（不提交）
```

### 5. 定期轮换密钥

定期更换密钥，特别是API密钥和Token。可以使用SecretsManager记录密钥的过期时间。

```python
from datetime import datetime, timedelta
from secrets_manager import SecretsManager

sm = SecretsManager()
sm.load()

# 记录密钥创建时间
key_created = datetime.strptime(sm.get('KEY_CREATED_AT'), '%Y-%m-%d')
max_age = timedelta(days=90)

if datetime.now() - key_created > max_age:
    print("⚠️  API密钥已超过90天，建议轮换")
```

## 与其他模块的集成

### 与四维防线的集成

四维防线第3层调用HardcodedDetector进行硬编码检测。

```python
from four_d_defense import RuleValidationLayer
from security.hardcoded_detector import HardcodedDetector

class RuleValidationLayer:
    def run_hardcoded_detection(self, output: str) -> HardcodedResult:
        """在规则校验层中使用硬编码检测"""
        detector = HardcodedDetector()

        # 将输出写入临时文件进行检测
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        temp_file.write(output)
        temp_file.close()

        try:
            report = detector.scan_file(Path(temp_file.name))
            return HardcodedResult(
                total_detections=len(report.detections),
                critical=sum(1 for d in report.detections if d.severity == Severity.CRITICAL),
                high=sum(1 for d in report.detections if d.severity == Severity.HIGH),
                detections=report.detections
            )
        finally:
            os.unlink(temp_file.name)
```

### 与资源协调器的集成

SECRET资源类型纳入MARC资源协调器管理。

```python
from resource_coordinator import ResourceCoordinator, ResourceType

coordinator = ResourceCoordinator()

# 注册密钥资源
coordinator.register_resource(
    resource_id='secret:api_key:github',
    type=ResourceType.SECRET,
    metadata={
        'key_type': 'api_key',
        'service': 'github',
        'read_once': True
    }
)

# 获取密钥（一次性使用）
lock_token = coordinator.acquire_lock(
    resource_id='secret:api_key:github',
    agent_id='api-client',
    lock_type=LockType.SHARED
)
```

## 故障排查

### 问题1: 密钥加载失败

**症状**: SecretsManager无法加载某些密钥。

**排查步骤**:
1. 检查.env文件是否存在且格式正确
2. 检查文件编码是否为UTF-8
3. 检查是否有语法错误（如未闭合的引号）
4. 检查是否有BOM标记

**解决方案**:
```python
# 调试加载过程
sm = SecretsManager()
try:
    sm.load()
except Exception as e:
    print(f"加载失败: {e}")

# 手动检查文件
with open('.env', 'r', encoding='utf-8-sig') as f:  # utf-8-sig 处理BOM
    for i, line in enumerate(f, 1):
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            print(f"Line {i}: {key.strip()} = {sm.mask_for_log(value.strip())}")
```

### 问题2: 硬编码检测误报

**症状**: HardcodedDetector报告了非敏感信息的误报。

**排查步骤**:
1. 查看具体检测到的内容和上下文
2. 判断是否真的是敏感信息
3. 如果不是，可以添加排除规则

**解决方案**:
```python
# 自定义排除规则
detector = HardcodedDetector(exclude_patterns=[
    (r'DEBUG\s*=\s*True', '调试标志'),
    (r'TEST_MODE\s*=\s*[Tt]rue', '测试模式'),
    (r'version\s*=\s*["\']?\d+\.\d+', '版本号')
])

report = detector.scan_directory(Path('.'))
```

### 问题3: 性能问题

**症状**: 大型项目扫描耗时过长。

**解决方案**:
```python
# 限制扫描范围
detector = HardcodedDetector()

# 只扫描特定目录
report = detector.scan_directory(Path('./src'))

# 并行扫描
from concurrent.futures import ThreadPoolExecutor, as_completed

def scan_subdir(subdir):
    return detector.scan_directory(subdir)

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(scan_subdir, d) for d in Path('./src').iterdir() if d.is_dir()]
    reports = [f.result() for f in as_completed(futures)]

# 合并报告
combined = DetectionReport(detections=[])
for r in reports:
    combined.detections.extend(r.detections)
```

## 总结

密钥与环境变量管理系统是Sanliu v4.0的安全基础设施，通过SecretsManager、HardcodedDetector、ConfigSecurityAuditor和EnvTemplateGenerator四个子系统，提供完整的密钥生命周期管理能力。该系统具有以下特点:

- **全面性**: 覆盖密钥的加载、存储、访问、检测、审计全流程
- **安全性**: 内置25种硬编码检测模式和严格的安全策略
- **易用性**: 提供简单的API接口和自动化工具
- **可扩展性**: 支持自定义检测模式和排除规则
- **合规性**: 符合安全最佳实践和行业标准

通过合理配置和使用密钥管理系统，可以有效防止敏感信息泄露，提高项目的安全性。
