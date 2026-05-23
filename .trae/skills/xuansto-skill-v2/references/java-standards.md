# Java 开发规范

> 版本: 1.9.0 | 更新日期: 2026-04-17 | 编码: UTF-8 without BOM | 行尾: LF

---

## 目录

1. [命名约定与代码风格](#1-命名约定与代码风格)
2. [项目结构规范](#2-项目结构规范)
3. [依赖管理规范](#3-依赖管理规范)
4. [测试规范](#4-测试规范)
5. [安全规范](#5-安全规范)
6. [常见框架规范](#6-常见框架规范)
7. [检查清单](#7-检查清单)

---

## 1. 命名约定与代码风格

### 1.1 命名约定

| 类型 | 命名规则 | 示例 |
|------|----------|------|
| 包名 | 全小写，使用点分隔 | `com.example.project.service` |
| 类名 | PascalCase | `UserService`, `OrderController` |
| 接口名 | PascalCase，可用 I 前缀 | `UserRepository`, `IUserService` |
| 方法名 | camelCase，动词开头 | `getUserById()`, `calculateTotal()` |
| 变量名 | camelCase | `userName`, `orderList` |
| 常量名 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| 枚举名 | PascalCase，值 UPPER_SNAKE_CASE | `enum Status { ACTIVE, INACTIVE }` |
| 泛型类型 | 单个大写字母或 PascalCase | `T`, `E`, `K`, `V`, `ResponseType` |

### 1.2 代码风格

#### 1.2.1 缩进与格式

```java
public class UserService {
    private static final int MAX_RETRY_COUNT = 3;
    private static final Logger logger = LoggerFactory.getLogger(UserService.class);
    
    private final UserRepository userRepository;
    private final EmailService emailService;
    
    public UserService(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
    
    public Optional<User> findUserById(Long id) {
        if (id == null || id <= 0) {
            logger.warn("Invalid user id: {}", id);
            return Optional.empty();
        }
        
        return userRepository.findById(id)
            .filter(user -> user.isActive())
            .map(this::enrichUserData);
    }
    
    private User enrichUserData(User user) {
        user.setLastAccessTime(LocalDateTime.now());
        return user;
    }
}
```

#### 1.2.2 大括号规则

```java
// 推荐: K&R 风格 (左大括号不换行)
if (condition) {
    doSomething();
} else {
    doOther();
}

// 禁止: 省略大括号
if (condition) doSomething();  // 错误

// 空块可以简洁
public void doNothing() {}
```

#### 1.2.3 行长度与换行

```java
// 最大行长度: 120 字符
// 方法链式调用换行
String result = users.stream()
    .filter(User::isActive)
    .map(User::getName)
    .collect(Collectors.joining(", "));

// 参数过多时换行
public User createUser(
    String name,
    String email,
    String phone,
    Address address
) {
    // ...
}
```

#### 1.2.4 导入顺序

```java
// 1. java.*
import java.util.List;
import java.util.Optional;

// 2. javax.*
import javax.validation.constraints.NotNull;

// 3. 第三方库
import org.springframework.stereotype.Service;
import lombok.RequiredArgsConstructor;

// 4. 本项目
import com.example.project.model.User;
import com.example.project.repository.UserRepository;

// 禁止使用通配符导入
import java.util.*;  // 错误
```

### 1.3 最佳实践

```java
// 使用 Optional 处理可能为空的返回值
public Optional<User> findUser(Long id) {
    return userRepository.findById(id);
}

// 使用 try-with-resources 管理资源
public String readFile(Path path) throws IOException {
    try (BufferedReader reader = Files.newBufferedReader(path)) {
        return reader.lines().collect(Collectors.joining("\n"));
    }
}

// 使用 StringBuilder 构建字符串
public String buildMessage(List<String> parts) {
    StringBuilder sb = new StringBuilder();
    for (String part : parts) {
        sb.append(part).append("\n");
    }
    return sb.toString();
}

// 优先使用不可变集合
public List<User> getActiveUsers() {
    return userRepository.findAll()
        .stream()
        .filter(User::isActive)
        .collect(Collectors.toUnmodifiableList());
}
```

---

## 2. 项目结构规范

### 2.1 Maven 标准布局

```
project-root/
├── pom.xml                          # Maven 配置文件
├── README.md                        # 项目说明
├── .gitignore                       # Git 忽略配置
├── docs/                            # 文档目录
│   ├── architecture/
│   └── api/
├── src/
│   ├── main/
│   │   ├── java/                    # 源代码
│   │   │   └── com/example/project/
│   │   │       ├── Application.java # 启动类
│   │   │       ├── config/          # 配置类
│   │   │       │   ├── SecurityConfig.java
│   │   │       │   └── DatabaseConfig.java
│   │   │       ├── controller/      # 控制器层
│   │   │       │   └── UserController.java
│   │   │       ├── service/         # 服务层
│   │   │       │   ├── UserService.java
│   │   │       │   └── impl/
│   │   │       │       └── UserServiceImpl.java
│   │   │       ├── repository/      # 数据访问层
│   │   │       │   └── UserRepository.java
│   │   │       ├── model/           # 领域模型
│   │   │       │   ├── User.java
│   │   │       │   └── dto/
│   │   │       │       ├── UserRequest.java
│   │   │       │       └── UserResponse.java
│   │   │       ├── exception/       # 异常处理
│   │   │       │   ├── GlobalExceptionHandler.java
│   │   │       │   └── ResourceNotFoundException.java
│   │   │       └── util/            # 工具类
│   │   │           └── DateUtils.java
│   │   └── resources/               # 资源文件
│   │       ├── application.yml      # 主配置
│   │       ├── application-dev.yml  # 开发环境配置
│   │       ├── application-prod.yml # 生产环境配置
│   │       ├── db/                  # 数据库脚本
│   │       │   └── migration/
│   │       └── static/              # 静态资源
│   └── test/
│       ├── java/                    # 测试代码
│       │   └── com/example/project/
│       │       ├── controller/
│       │       │   └── UserControllerTest.java
│       │       ├── service/
│       │       │   └── UserServiceTest.java
│       │       └── integration/
│       │           └── UserIntegrationTest.java
│       └── resources/               # 测试资源
│           └── application-test.yml
└── target/                          # 构建输出 (gitignore)
```

### 2.2 Gradle 标准布局

```
project-root/
├── build.gradle                     # Gradle 构建脚本
├── settings.gradle                  # 项目设置
├── gradle.properties                # Gradle 属性
├── gradlew                          # Gradle Wrapper (Unix)
├── gradlew.bat                      # Gradle Wrapper (Windows)
├── src/
│   ├── main/
│   │   ├── java/
│   │   └── resources/
│   └── test/
│       ├── java/
│       └── resources/
├── build/                           # 构建输出 (gitignore)
└── .gradle/                         # Gradle 缓存 (gitignore)
```

### 2.3 多模块项目结构

```
multi-module-project/
├── pom.xml                          # 父 POM
├── common/                          # 公共模块
│   ├── pom.xml
│   └── src/
│       ├── main/java/
│       └── test/java/
├── api/                             # API 模块
│   ├── pom.xml
│   └── src/
├── service/                         # 服务模块
│   ├── pom.xml
│   └── src/
├── web/                             # Web 模块
│   ├── pom.xml
│   └── src/
└── infrastructure/                  # 基础设施模块
    ├── pom.xml
    └── src/
```

---

## 3. 依赖管理规范

### 3.1 Maven 配置

#### 3.1.1 标准 pom.xml 结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>

    <groupId>com.example</groupId>
    <artifactId>project-name</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <name>Project Name</name>
    <description>Project description</description>

    <properties>
        <java.version>21</java.version>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
        <lombok.version>1.18.30</lombok.version>
        <mapstruct.version>1.5.5.Final</mapstruct.version>
    </properties>

    <dependencies>
        <!-- Spring Boot Starters -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <version>${lombok.version}</version>
            <scope>provided</scope>
        </dependency>

        <!-- MapStruct -->
        <dependency>
            <groupId>org.mapstruct</groupId>
            <artifactId>mapstruct</artifactId>
            <version>${mapstruct.version}</version>
        </dependency>

        <!-- Test Dependencies -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
            
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <configuration>
                    <source>${java.version}</source>
                    <target>${java.version}</target>
                    <annotationProcessorPaths>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                            <version>${lombok.version}</version>
                        </path>
                        <path>
                            <groupId>org.mapstruct</groupId>
                            <artifactId>mapstruct-processor</artifactId>
                            <version>${mapstruct.version}</version>
                        </path>
                    </annotationProcessorPaths>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

#### 3.1.2 依赖管理原则

```xml
<!-- 使用 dependencyManagement 统一版本 -->
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-dependencies</artifactId>
            <version>3.2.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<!-- 排除冲突依赖 -->
<dependency>
    <groupId>com.example</groupId>
    <artifactId>some-library</artifactId>
    <exclusions>
        <exclusion>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-log4j12</artifactId>
        </exclusion>
    </exclusions>
</dependency>
```

### 3.2 Gradle 配置

#### 3.2.1 标准 build.gradle 结构

```groovy
plugins {
    id 'java'
    id 'org.springframework.boot' version '3.2.0'
    id 'io.spring.dependency-management' version '1.1.4'
}

group = 'com.example'
version = '1.0.0-SNAPSHOT'

java {
    sourceCompatibility = '21'
    targetCompatibility = '21'
}

configurations {
    compileOnly {
        extendsFrom annotationProcessor
    }
}

repositories {
    mavenCentral()
    maven { url 'https://repo.spring.io/milestone' }
}

ext {
    set('lombokVersion', '1.18.30')
    set('mapstructVersion', '1.5.5.Final')
}

dependencies {
    // Spring Boot Starters
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-validation'
    
    // Lombok
    compileOnly "org.projectlombok:lombok:${lombokVersion}"
    annotationProcessor "org.projectlombok:lombok:${lombokVersion}"
    
    // MapStruct
    implementation "org.mapstruct:mapstruct:${mapstructVersion}"
    annotationProcessor "org.mapstruct:mapstruct-processor:${mapstructVersion}"
    
    // Test
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}

tasks.named('test') {
    useJUnitPlatform()
}

tasks.withType(JavaCompile) {
    options.encoding = 'UTF-8'
}

bootJar {
    archiveFileName = "${project.name}.jar"
}
```

#### 3.2.2 Gradle Kotlin DSL

```kotlin
plugins {
    java
    id("org.springframework.boot") version "3.2.0"
    id("io.spring.dependency-management") version "1.1.4"
}

group = "com.example"
version = "1.0.0-SNAPSHOT"

java {
    sourceCompatibility = JavaVersion.VERSION_21
}

repositories {
    mavenCentral()
}

val lombokVersion = "1.18.30"
val mapstructVersion = "1.5.5.Final"

dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")
    implementation("org.springframework.boot:spring-boot-starter-data-jpa")
    
    compileOnly("org.projectlombok:lombok:$lombokVersion")
    annotationProcessor("org.projectlombok:lombok:$lombokVersion")
    
    testImplementation("org.springframework.boot:spring-boot-starter-test")
}

tasks.withType<Test> {
    useJUnitPlatform()
}
```

### 3.3 依赖版本管理

```yaml
# 推荐版本组合 (Spring Boot 3.2.x)
versions:
  java: 21
  spring-boot: 3.2.0
  spring-security: 6.2.0
  hibernate: 6.4.0
  junit: 5.10.0
  mockito: 5.8.0
  lombok: 1.18.30
  mapstruct: 1.5.5.Final
  checkstyle: 10.12.0
  spotbugs: 4.8.0
```

---

## 4. 测试规范

### 4.1 JUnit 5 规范

#### 4.1.1 测试类结构

```java
@DisplayName("UserService 测试")
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @InjectMocks
    private UserService userService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Nested
    @DisplayName("findUserById 方法测试")
    class FindUserByIdTests {

        @Test
        @DisplayName("当用户存在时返回用户")
        void shouldReturnUser_WhenUserExists() {
            // Arrange
            Long userId = 1L;
            User expectedUser = User.builder()
                .id(userId)
                .name("张三")
                .email("zhangsan@example.com")
                .build();
            
            when(userRepository.findById(userId)).thenReturn(Optional.of(expectedUser));

            // Act
            Optional<User> result = userService.findUserById(userId);

            // Assert
            assertThat(result).isPresent();
            assertThat(result.get().getName()).isEqualTo("张三");
            
            verify(userRepository).findById(userId);
        }

        @Test
        @DisplayName("当用户不存在时返回空")
        void shouldReturnEmpty_WhenUserNotFound() {
            // Arrange
            Long userId = 999L;
            when(userRepository.findById(userId)).thenReturn(Optional.empty());

            // Act
            Optional<User> result = userService.findUserById(userId);

            // Assert
            assertThat(result).isEmpty();
        }

        @ParameterizedTest
        @ValueSource(longs = {0, -1, -100})
        @DisplayName("当ID无效时返回空")
        void shouldReturnEmpty_WhenIdIsInvalid(Long invalidId) {
            Optional<User> result = userService.findUserById(invalidId);
            assertThat(result).isEmpty();
            verify(userRepository, never()).findById(any());
        }
    }
}
```

#### 4.1.2 参数化测试

```java
@ParameterizedTest
@MethodSource("provideUserScenarios")
@DisplayName("用户创建场景测试")
void shouldCreateUser_WithVariousScenarios(String name, String email, boolean expectedValid) {
    // Arrange
    UserRequest request = new UserRequest(name, email);

    // Act & Assert
    if (expectedValid) {
        assertThatCode(() -> userService.createUser(request))
            .doesNotThrowAnyException();
    } else {
        assertThatThrownBy(() -> userService.createUser(request))
            .isInstanceOf(ValidationException.class);
    }
}

private static Stream<Arguments> provideUserScenarios() {
    return Stream.of(
        Arguments.of("张三", "zhangsan@example.com", true),
        Arguments.of("", "zhangsan@example.com", false),
        Arguments.of("张三", "invalid-email", false),
        Arguments.of(null, "zhangsan@example.com", false)
    );
}
```

### 4.2 Mockito 规范

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;

    @Spy
    private PaymentProcessor paymentProcessor = new PaymentProcessor();

    @Captor
    private ArgumentCaptor<Order> orderCaptor;

    @InjectMocks
    private OrderService orderService;

    @Test
    @DisplayName("创建订单时应该发送通知")
    void shouldSendNotification_WhenOrderCreated() {
        // Arrange
        OrderRequest request = new OrderRequest("PROD-001", 2);
        Order savedOrder = Order.builder()
            .id(1L)
            .productCode("PROD-001")
            .quantity(2)
            .build();
        
        when(orderRepository.save(any(Order.class))).thenReturn(savedOrder);

        // Act
        orderService.createOrder(request);

        // Assert
        verify(orderRepository).save(orderCaptor.capture());
        Order capturedOrder = orderCaptor.getValue();
        
        assertThat(capturedOrder.getProductCode()).isEqualTo("PROD-001");
        assertThat(capturedOrder.getQuantity()).isEqualTo(2);
        
        verify(paymentProcessor).processPayment(any());
    }

    @Test
    @DisplayName("支付失败时应该回滚订单")
    void shouldRollbackOrder_WhenPaymentFails() {
        // Arrange
        OrderRequest request = new OrderRequest("PROD-001", 2);
        
        when(orderRepository.save(any())).thenAnswer(invocation -> {
            Order order = invocation.getArgument(0);
            order.setId(1L);
            return order;
        });
        
        doThrow(new PaymentException("Payment failed"))
            .when(paymentProcessor).processPayment(any());

        // Act & Assert
        assertThatThrownBy(() -> orderService.createOrder(request))
            .isInstanceOf(OrderException.class)
            .hasCauseInstanceOf(PaymentException.class);
        
        verify(orderRepository).deleteById(1L);
    }
}
```

### 4.3 集成测试规范

```java
@SpringBootTest
@Testcontainers
@AutoConfigureMockMvc
class UserIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void cleanUp() {
        userRepository.deleteAll();
    }

    @Test
    @DisplayName("创建用户API集成测试")
    void shouldCreateUser_WhenValidRequest() throws Exception {
        String requestBody = """
            {
                "name": "张三",
                "email": "zhangsan@example.com"
            }
            """;

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestBody))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("张三"))
            .andExpect(jsonPath("$.email").value("zhangsan@example.com"))
            .andExpect(jsonPath("$.id").exists());

        assertThat(userRepository.count()).isEqualTo(1);
    }

    @Test
    @DisplayName("获取用户列表分页测试")
    void shouldReturnPaginatedUsers() throws Exception {
        // Arrange
        for (int i = 0; i < 25; i++) {
            User user = User.builder()
                .name("用户" + i)
                .email("user" + i + "@example.com")
                .build();
            userRepository.save(user);
        }

        // Act & Assert
        mockMvc.perform(get("/api/users")
                .param("page", "0")
                .param("size", "10"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").isArray())
            .andExpect(jsonPath("$.content.length()").value(10))
            .andExpect(jsonPath("$.totalElements").value(25))
            .andExpect(jsonPath("$.totalPages").value(3));
    }
}
```

### 4.4 测试命名约定

```java
// 测试方法命名模式: should[ExpectedBehavior]_When[Condition]
@Test
void shouldThrowException_WhenUserNotFound() { }

@Test
void shouldReturnTrue_WhenEmailIsValid() { }

@Test
void shouldCreateOrder_WhenPaymentSucceeds() { }

// 或者使用 given-when-then 模式
@Test
@DisplayName("Given valid user request When create user Then return created user")
void givenValidUserRequest_whenCreateUser_thenReturnCreatedUser() { }
```

---

## 5. 安全规范

### 5.1 OWASP Java 安全检查清单

#### 5.1.1 输入验证

```java
// 使用 Bean Validation
public class UserRequest {
    
    @NotBlank(message = "用户名不能为空")
    @Size(min = 2, max = 50, message = "用户名长度必须在2-50之间")
    @Pattern(regexp = "^[a-zA-Z0-9_]+$", message = "用户名只能包含字母、数字和下划线")
    private String name;
    
    @NotBlank(message = "邮箱不能为空")
    @Email(message = "邮箱格式不正确")
    private String email;
    
    @NotBlank(message = "密码不能为空")
    @Size(min = 8, max = 100, message = "密码长度必须在8-100之间")
    @Pattern(regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).+$", 
             message = "密码必须包含大小写字母和数字")
    private String password;
}

// 自定义验证器
public class SecureInputValidator {
    
    private static final Pattern SQL_INJECTION_PATTERN = 
        Pattern.compile("('|(--)|;|(\\|\\|)|(\\*))", Pattern.CASE_INSENSITIVE);
    
    private static final Pattern XSS_PATTERN = 
        Pattern.compile("<script.*?>.*?</script>", Pattern.CASE_INSENSITIVE);
    
    public static boolean isSafe(String input) {
        if (input == null) return true;
        return !SQL_INJECTION_PATTERN.matcher(input).find() 
            && !XSS_PATTERN.matcher(input).find();
    }
}
```

#### 5.1.2 SQL 注入防护

```java
// 正确: 使用参数化查询
@Repository
public class UserRepositoryImpl implements UserRepositoryCustom {
    
    @PersistenceContext
    private EntityManager entityManager;
    
    public List<User> findActiveUsersByRole(String role) {
        String jpql = "SELECT u FROM User u WHERE u.role = :role AND u.active = true";
        return entityManager.createQuery(jpql, User.class)
            .setParameter("role", role)
            .getResultList();
    }
}

// 正确: 使用 Spring Data JPA
public interface UserRepository extends JpaRepository<User, Long> {
    
    @Query("SELECT u FROM User u WHERE u.email = :email AND u.active = true")
    Optional<User> findActiveByEmail(@Param("email") String email);
    
    List<User> findByRoleAndActiveTrue(String role);
}

// 错误: 字符串拼接 (禁止)
public User findByEmail(String email) {
    String sql = "SELECT * FROM users WHERE email = '" + email + "'"; // 危险!
    // ...
}
```

#### 5.1.3 XSS 防护

```java
// 使用 OWASP Java Encoder
import org.owasp.encoder.Encode;

public class SafeOutputUtil {
    
    public static String escapeHtml(String input) {
        return Encode.forHtml(input);
    }
    
    public static String escapeJavaScript(String input) {
        return Encode.forJavaScript(input);
    }
    
    public static String escapeAttribute(String input) {
        return Encode.forHtmlAttribute(input);
    }
}

// 在 Controller 中使用
@RestController
public class UserController {
    
    @GetMapping("/search")
    public ResponseEntity<String> search(@RequestParam String q) {
        String safeQuery = Encode.forHtml(q);
        return ResponseEntity.ok("搜索结果: " + safeQuery);
    }
}
```

#### 5.1.4 密码安全

```java
// 使用 BCrypt 加密
@Service
public class PasswordService {
    
    private final BCryptPasswordEncoder encoder;
    
    public PasswordService() {
        this.encoder = new BCryptPasswordEncoder(12); // 强度 12
    }
    
    public String encode(String rawPassword) {
        return encoder.encode(rawPassword);
    }
    
    public boolean matches(String rawPassword, String encodedPassword) {
        return encoder.matches(rawPassword, encodedPassword);
    }
}

// 密码存储
@Entity
public class User {
    
    @Id
    private Long id;
    
    private String name;
    
    @JsonIgnore  // 永远不要返回密码
    private String passwordHash;  // 存储哈希值，不存储明文
    
    public void setPassword(String password) {
        this.passwordHash = passwordService.encode(password);
    }
}
```

### 5.2 Spring Security 配置

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf
                .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            )
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .requestMatchers("/api/user/**").hasAnyRole("USER", "ADMIN")
                .anyRequest().authenticated()
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .headers(headers -> headers
                .contentSecurityPolicy(csp -> csp
                    .policyDirectives("default-src 'self'; script-src 'self' 'unsafe-inline'")
                )
                .frameOptions(HeadersConfigurer.FrameOptionsConfig::deny)
                .httpStrictTransportSecurity(hsts -> hsts
                    .includeSubDomains(true)
                    .maxAgeInSeconds(31536000)
                )
            )
            .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);
        
        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter() {
        return new JwtAuthenticationFilter();
    }
}
```

### 5.3 敏感数据处理

```java
// 日志脱敏
@Slf4j
public class SecureLogger {
    
    private static final Pattern EMAIL_PATTERN = 
        Pattern.compile("(\\w{1,3})\\w+@(\\w+)");
    private static final Pattern PHONE_PATTERN = 
        Pattern.compile("(\\d{3})\\d{4}(\\d{4})");
    private static final Pattern ID_CARD_PATTERN = 
        Pattern.compile("(\\d{4})\\d{10}(\\d{4})");
    
    public static String maskEmail(String email) {
        if (email == null) return null;
        return EMAIL_PATTERN.matcher(email).replaceAll("$1***@$2");
    }
    
    public static String maskPhone(String phone) {
        if (phone == null) return null;
        return PHONE_PATTERN.matcher(phone).replaceAll("$1****$2");
    }
    
    public static String maskIdCard(String idCard) {
        if (idCard == null) return null;
        return ID_CARD_PATTERN.matcher(idCard).replaceAll("$1**********$2");
    }
}

// 使用示例
log.info("用户注册: email={}, phone={}", 
    SecureLogger.maskEmail(email), 
    SecureLogger.maskPhone(phone));
```

---

## 6. 常见框架规范

### 6.1 Spring Boot 规范

#### 6.1.1 应用配置

```yaml
# application.yml
spring:
  application:
    name: project-name
  
  profiles:
    active: dev
  
  datasource:
    url: jdbc:postgresql://${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME:projectdb}
    username: ${DB_USERNAME:postgres}
    password: ${DB_PASSWORD:password}
    driver-class-name: org.postgresql.Driver
    hikari:
      maximum-pool-size: 10
      minimum-idle: 5
      idle-timeout: 300000
      connection-timeout: 20000
  
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    properties:
      hibernate:
        format_sql: true
        dialect: org.hibernate.dialect.PostgreSQLDialect
  
  jackson:
    serialization:
      write-dates-as-timestamps: false
    property-naming-strategy: SNAKE_CASE
    default-property-inclusion: non_null

server:
  port: ${SERVER_PORT:8080}
  servlet:
    context-path: /api
  
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      show-details: when-authorized

logging:
  level:
    root: INFO
    com.example.project: DEBUG
    org.hibernate.SQL: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
```

#### 6.1.2 分层架构

```java
// Controller 层
@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Tag(name = "用户管理", description = "用户相关API")
public class UserController {

    private final UserService userService;

    @PostMapping
    @Operation(summary = "创建用户")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "创建成功"),
        @ApiResponse(responseCode = "400", description = "请求参数错误"),
        @ApiResponse(responseCode = "409", description = "用户已存在")
    })
    public ResponseEntity<UserResponse> createUser(
        @Valid @RequestBody UserRequest request
    ) {
        UserResponse response = userService.createUser(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/{id}")
    @Operation(summary = "获取用户详情")
    public ResponseEntity<UserResponse> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.getUserById(id));
    }

    @GetMapping
    @Operation(summary = "分页查询用户")
    public ResponseEntity<PageResponse<UserResponse>> getUsers(
        @RequestParam(defaultValue = "0") int page,
        @RequestParam(defaultValue = "10") int size,
        @RequestParam(required = false) String name
    ) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
        return ResponseEntity.ok(userService.getUsers(name, pageable));
    }
}

// Service 层
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final UserMapper userMapper;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    @Transactional
    public UserResponse createUser(UserRequest request) {
        validateUserNotExists(request.getEmail());
        
        User user = userMapper.toEntity(request);
        user.setPassword(encodePassword(request.getPassword()));
        
        User savedUser = userRepository.save(user);
        
        eventPublisher.publishEvent(new UserCreatedEvent(savedUser.getId()));
        
        return userMapper.toResponse(savedUser);
    }

    @Override
    public UserResponse getUserById(Long id) {
        return userRepository.findById(id)
            .map(userMapper::toResponse)
            .orElseThrow(() -> new ResourceNotFoundException("用户不存在: " + id));
    }

    private void validateUserNotExists(String email) {
        if (userRepository.existsByEmail(email)) {
            throw new ConflictException("邮箱已被注册: " + email);
        }
    }
}

// Repository 层
@Repository
public interface UserRepository extends JpaRepository<User, Long>, UserRepositoryCustom {
    
    boolean existsByEmail(String email);
    
    Optional<User> findByEmailAndActiveTrue(String email);
    
    @Query("SELECT u FROM User u WHERE " +
           "(:name IS NULL OR LOWER(u.name) LIKE LOWER(CONCAT('%', :name, '%'))) " +
           "AND u.active = true")
    Page<User> findByNameContaining(@Param("name") String name, Pageable pageable);
}
```

#### 6.1.3 异常处理

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleResourceNotFound(ResourceNotFoundException ex) {
        ErrorResponse error = ErrorResponse.builder()
            .timestamp(LocalDateTime.now())
            .status(HttpStatus.NOT_FOUND.value())
            .error("资源未找到")
            .message(ex.getMessage())
            .path(getCurrentRequestPath())
            .build();
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationErrors(MethodArgumentNotValidException ex) {
        List<String> errors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(error -> error.getField() + ": " + error.getDefaultMessage())
            .toList();
        
        ErrorResponse error = ErrorResponse.builder()
            .timestamp(LocalDateTime.now())
            .status(HttpStatus.BAD_REQUEST.value())
            .error("参数验证失败")
            .message(String.join("; ", errors))
            .path(getCurrentRequestPath())
            .build();
        return ResponseEntity.badRequest().body(error);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex) {
        log.error("未处理的异常", ex);
        
        ErrorResponse error = ErrorResponse.builder()
            .timestamp(LocalDateTime.now())
            .status(HttpStatus.INTERNAL_SERVER_ERROR.value())
            .error("服务器内部错误")
            .message("系统繁忙，请稍后重试")
            .path(getCurrentRequestPath())
            .build();
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }

    private String getCurrentRequestPath() {
        ServletRequestAttributes attributes = (ServletRequestAttributes) 
            RequestContextHolder.getRequestAttributes();
        return attributes != null ? attributes.getRequest().getRequestURI() : "unknown";
    }
}
```

### 6.2 Quarkus 规范

#### 6.2.1 应用配置

```properties
# application.properties
quarkus.application.name=project-name
quarkus.http.port=8080
quarkus.http.root-path=/api

# 数据源配置
quarkus.datasource.db-kind=postgresql
quarkus.datasource.username=${DB_USERNAME:postgres}
quarkus.datasource.password=${DB_PASSWORD:password}
quarkus.datasource.jdbc.url=jdbc:postgresql://${DB_HOST:localhost}:${DB_PORT:5432}/${DB_NAME:projectdb}

# Hibernate
quarkus.hibernate-orm.database.generation=validate
quarkus.hibernate-orm.log.sql=true

# 健康检查
quarkus.smallrye-health.root-path=/health
quarkus.smallrye-health.liveness-path=/liveness
quarkus.smallrye-health.readiness-path=/readiness

# 指标
quarkus.micrometer.enabled=true
quarkus.micrometer.export.prometheus.enabled=true

# OpenAPI
quarkus.swagger-ui.always-include=true
mp.openapi.extensions.smallrye.info.title=Project API
mp.openapi.extensions.smallrye.info.version=1.0.0
```

#### 6.2.2 REST 实现

```java
@Path("/api/v1/users")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
@RequiredArgsConstructor
public class UserResource {

    private final UserService userService;

    @POST
    @ResponseStatus(HttpStatus.CREATED)
    @Operation(summary = "创建用户")
    public UserResponse create(@Valid UserRequest request) {
        return userService.createUser(request);
    }

    @GET
    @Path("/{id}")
    @Operation(summary = "获取用户详情")
    public UserResponse get(@PathParam("id") Long id) {
        return userService.getUserById(id);
    }

    @GET
    @Operation(summary = "分页查询用户")
    public PageResponse<UserResponse> list(
        @QueryParam("page") @DefaultValue("0") int page,
        @QueryParam("size") @DefaultValue("10") int size,
        @QueryParam("name") String name
    ) {
        return userService.getUsers(name, PageRequest.of(page, size));
    }

    @PUT
    @Path("/{id}")
    @Operation(summary = "更新用户")
    public UserResponse update(@PathParam("id") Long id, @Valid UserRequest request) {
        return userService.updateUser(id, request);
    }

    @DELETE
    @Path("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "删除用户")
    public void delete(@PathParam("id") Long id) {
        userService.deleteUser(id);
    }
}

// Panache Repository
@ApplicationScoped
public class UserRepository implements PanacheRepository<User> {
    
    public boolean existsByEmail(String email) {
        return find("email", email).count() > 0;
    }
    
    public Optional<User> findByEmail(String email) {
        return find("email = ?1 and active = true", email).firstResultOptional();
    }
    
    public PanacheQuery<User> findByNameContaining(String name, Page page) {
        if (name == null || name.isBlank()) {
            return findAll().page(page);
        }
        return find("lower(name) like lower(?1)", "%" + name + "%").page(page);
    }
}
```

#### 6.2.3 响应式编程

```java
@Path("/api/v1/orders")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class OrderResource {

    @Inject
    OrderService orderService;

    @GET
    @Path("/{id}")
    @NonBlocking
    public Uni<OrderResponse> get(@PathParam("id") Long id) {
        return orderService.getOrderById(id);
    }

    @POST
    public Uni<Response> create(@Valid OrderRequest request) {
        return orderService.createOrder(request)
            .map(order -> Response.status(Response.Status.CREATED)
                .entity(order)
                .build())
            .onFailure(ValidationException.class)
            .recoverWithItem(throwable -> 
                Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", throwable.getMessage()))
                    .build());
    }
}

@ApplicationScoped
public class OrderService {

    @Inject
    OrderRepository orderRepository;

    @Inject
    @Channel("order-events")
    Emitter<OrderEvent> eventEmitter;

    public Uni<OrderResponse> getOrderById(Long id) {
        return orderRepository.findById(id)
            .map(this::toResponse)
            .onItem().ifNull().failWith(() -> 
                new NotFoundException("订单不存在: " + id));
    }

    public Uni<OrderResponse> createOrder(OrderRequest request) {
        return Uni.createFrom().item(() -> validateAndCreate(request))
            .flatMap(orderRepository::persist)
            .invoke(order -> eventEmitter.send(new OrderCreatedEvent(order.id)))
            .map(this::toResponse);
    }
}
```

---

## 7. 检查清单

### 7.1 代码风格检查清单

- [ ] 类名使用 PascalCase
- [ ] 方法名和变量名使用 camelCase
- [ ] 常量使用 UPPER_SNAKE_CASE
- [ ] 包名全小写
- [ ] 方法长度不超过 50 行
- [ ] 类长度不超过 500 行
- [ ] 方法参数不超过 4 个
- [ ] 避免深层嵌套（最多 3 层）
- [ ] 使用有意义的命名
- [ ] 删除未使用的代码和导入

### 7.2 安全检查清单

- [ ] 所有用户输入都经过验证
- [ ] 使用参数化查询防止 SQL 注入
- [ ] 密码使用 BCrypt 加密存储
- [ ] 敏感数据不在日志中输出
- [ ] API 返回数据不包含敏感字段
- [ ] 配置文件中的密码使用环境变量
- [ ] 启用 CSRF 防护
- [ ] 配置 CSP 头
- [ ] 启用 HSTS
- [ ] 使用 HTTPS

### 7.3 测试检查清单

- [ ] 单元测试覆盖核心业务逻辑
- [ ] 测试覆盖率 ≥ 80%
- [ ] 测试方法命名清晰
- [ ] 使用参数化测试覆盖边界情况
- [ ] Mock 外部依赖
- [ ] 集成测试使用 Testcontainers
- [ ] 测试数据使用 Fixture 或 Builder
- [ ] 测试相互独立，可并行执行
- [ ] 清理测试数据

### 7.4 依赖管理检查清单

- [ ] 使用依赖管理 BOM
- [ ] 版本号在 properties 中统一管理
- [ ] 定期更新依赖版本
- [ ] 使用 OWASP Dependency Check 扫描漏洞
- [ ] 排除冲突依赖
- [ ] 不使用 SNAPSHOT 版本（生产环境）

### 7.5 Spring Boot 检查清单

- [ ] 配置使用外部化
- [ ] 使用 Profile 区分环境
- [ ] 健康检查端点配置
- [ ] 优雅关闭配置
- [ ] 日志级别合理
- [ ] 数据库连接池配置
- [ ] 异常处理统一
- [ ] API 文档生成

### 7.6 Quarkus 检查清单

- [ ] 使用 native image 优化启动
- [ ] 配置健康检查
- [ ] 使用 Panache 简化数据访问
- [ ] 响应式端点使用 Uni/Multi
- [ ] 配置指标导出
- [ ] OpenAPI 文档配置

---

## 附录

### A. 常用工具

| 工具 | 用途 | 配置文件 |
|------|------|----------|
| Checkstyle | 代码风格检查 | `checkstyle.xml` |
| SpotBugs | 静态分析 | `spotbugs-exclude.xml` |
| PMD | 代码质量检查 | `pmd-ruleset.xml` |
| OWASP Dependency Check | 依赖漏洞扫描 | Maven/Gradle 插件 |
| JaCoCo | 测试覆盖率 | Maven/Gradle 插件 |
| Spotless | 代码格式化 | Maven/Gradle 插件 |

### B. 参考资源

- [Oracle Java Code Conventions](https://www.oracle.com/java/technologies/javase/codeconventions-contents.html)
- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- [Spring Boot Reference](https://docs.spring.io/spring-boot/docs/current/reference/html/)
- [Quarkus Guides](https://quarkus.io/guides/)
- [OWASP Java Security](https://owasp.org/www-project-java-security/)
- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)

---

*文档维护: Xuansto Skill | 最后更新: 2026-04-17*
