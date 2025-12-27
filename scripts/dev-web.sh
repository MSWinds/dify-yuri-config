#!/bin/bash
# Dify Web 前端开发辅助脚本
# 使用方法: ./scripts/dev-web.sh [command]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/web"
DOCKER_DIR="$PROJECT_ROOT/docker"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

print_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

print_error() {
    echo -e "${RED}✗ ${NC}$1"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 检查依赖
check_dependencies() {
    print_header "检查依赖"
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    REQUIRED_VERSION="22.11.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Node.js 版本过低: $NODE_VERSION (需要 >= $REQUIRED_VERSION)"
        exit 1
    fi
    print_success "Node.js 版本: $NODE_VERSION"
    
    # 检查 pnpm
    if ! command -v pnpm &> /dev/null; then
        print_error "pnpm 未安装"
        print_info "运行: npm install -g pnpm@10"
        exit 1
    fi
    print_success "pnpm 版本: $(pnpm --version)"
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker 未安装（部署时需要）"
    else
        print_success "Docker 版本: $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
    fi
}

# 首次设置
setup() {
    print_header "首次设置"
    
    check_dependencies
    
    cd "$WEB_DIR"
    
    # 安装依赖
    print_info "安装依赖..."
    pnpm install
    print_success "依赖安装完成"
    
    # 创建 .env.local
    if [ ! -f ".env.local" ]; then
        print_info "创建 .env.local..."
        
        # 获取主机 IP（用于虚拟机环境）
        HOST_IP=$(hostname -I | awk '{print $1}')
        if [ -z "$HOST_IP" ]; then
            HOST_IP="localhost"
        fi
        
        cat > .env.local << EOF
# 开发环境配置
NEXT_PUBLIC_DEPLOY_ENV=DEVELOPMENT
NEXT_PUBLIC_EDITION=SELF_HOSTED

# 连接到本地 Docker 后端 API
# 如果在虚拟机中，使用虚拟机 IP: ${HOST_IP}
# 如果在本机，使用 localhost
NEXT_PUBLIC_API_PREFIX=http://${HOST_IP}/console/api
NEXT_PUBLIC_PUBLIC_API_PREFIX=http://${HOST_IP}/api

# Cookie 域名（本地开发留空）
NEXT_PUBLIC_COOKIE_DOMAIN=

# Sentry（本地开发留空）
NEXT_PUBLIC_SENTRY_DSN=
EOF
        print_success ".env.local 创建完成"
        print_info "API 地址: http://${HOST_IP}/console/api"
    else
        print_warning ".env.local 已存在，跳过创建"
    fi
    
    print_success "设置完成！"
    print_info "运行 './scripts/dev-web.sh dev' 启动开发服务器"
}

# 启动开发服务器
dev() {
    print_header "启动开发服务器"
    
    cd "$WEB_DIR"
    
    if [ ! -f ".env.local" ]; then
        print_error ".env.local 不存在"
        print_info "运行 './scripts/dev-web.sh setup' 进行首次设置"
        exit 1
    fi
    
    print_info "启动 Next.js 开发服务器..."
    print_info "访问 http://localhost:3000"
    print_warning "按 Ctrl+C 停止服务器"
    echo ""
    
    pnpm dev
}

# 代码检查
check() {
    print_header "代码检查"
    
    cd "$WEB_DIR"
    
    print_info "运行 ESLint..."
    pnpm lint:fix
    print_success "ESLint 检查通过"
    
    print_info "运行 TypeScript 类型检查..."
    pnpm type-check:tsgo
    print_success "TypeScript 检查通过"
    
    print_info "检查 i18n 完整性..."
    pnpm check-i18n
    print_success "i18n 检查通过"
    
    print_success "所有检查通过！"
}

# 运行测试
test() {
    print_header "运行测试"
    
    cd "$WEB_DIR"
    
    if [ "$1" == "watch" ]; then
        print_info "启动测试监听模式..."
        pnpm test:watch
    elif [ "$1" == "coverage" ]; then
        print_info "运行测试并生成覆盖率报告..."
        pnpm test:coverage
    else
        print_info "运行所有测试..."
        pnpm test
        print_success "测试通过！"
    fi
}

# 构建测试
build() {
    print_header "构建测试"
    
    cd "$WEB_DIR"
    
    print_info "运行构建..."
    pnpm build
    print_success "构建成功！"
    
    print_info "构建产物位置: $WEB_DIR/.next"
}

# 部署到 Docker
deploy() {
    print_header "部署到 Docker"
    
    cd "$DOCKER_DIR"
    
    print_info "构建 Docker 镜像..."
    docker-compose build web
    print_success "镜像构建完成"
    
    print_info "启动容器..."
    docker-compose up -d web
    print_success "容器启动完成"
    
    print_info "等待服务就绪..."
    sleep 3
    
    print_info "查看日志..."
    docker-compose logs --tail=20 web
    
    print_success "部署完成！"
    print_info "访问 http://localhost"
}

# 完整流程（检查 + 测试 + 构建 + 部署）
full() {
    print_header "完整发布流程"
    
    check
    test
    build
    
    read -p "$(echo -e ${YELLOW}是否部署到 Docker? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        deploy
    else
        print_info "跳过部署"
    fi
}

# 查看日志
logs() {
    print_header "查看日志"
    
    cd "$DOCKER_DIR"
    
    if [ "$1" == "web" ]; then
        docker-compose logs -f web
    elif [ "$1" == "api" ]; then
        docker-compose logs -f api
    elif [ "$1" == "nginx" ]; then
        docker-compose logs -f nginx
    else
        docker-compose logs -f
    fi
}

# 清理
clean() {
    print_header "清理缓存"
    
    cd "$WEB_DIR"
    
    print_info "清理 Next.js 缓存..."
    rm -rf .next
    
    print_info "清理 node_modules..."
    rm -rf node_modules
    
    print_info "清理 pnpm-lock.yaml..."
    rm -f pnpm-lock.yaml
    
    print_success "清理完成！"
    print_info "运行 './scripts/dev-web.sh setup' 重新安装依赖"
}

# 状态检查
status() {
    print_header "系统状态"
    
    check_dependencies
    
    # 检查 .env.local
    if [ -f "$WEB_DIR/.env.local" ]; then
        print_success ".env.local 已配置"
    else
        print_warning ".env.local 未配置"
    fi
    
    # 检查 node_modules
    if [ -d "$WEB_DIR/node_modules" ]; then
        print_success "依赖已安装"
    else
        print_warning "依赖未安装"
    fi
    
    # 检查 Docker 服务
    cd "$DOCKER_DIR"
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker 服务运行中"
        docker-compose ps
    else
        print_warning "Docker 服务未运行"
    fi
}

# 帮助信息
show_help() {
    cat << EOF
Dify Web 前端开发辅助脚本

使用方法:
  ./scripts/dev-web.sh [command]

命令:
  setup         首次设置（安装依赖、创建配置）
  dev           启动开发服务器
  check         代码检查（lint + type-check + i18n）
  test [mode]   运行测试
                  - 无参数: 运行所有测试
                  - watch: 监听模式
                  - coverage: 生成覆盖率报告
  build         构建测试
  deploy        部署到 Docker
  full          完整流程（检查 + 测试 + 构建 + 部署）
  logs [service] 查看日志
                  - web: 前端日志
                  - api: 后端日志
                  - nginx: nginx 日志
                  - 无参数: 所有日志
  clean         清理缓存和依赖
  status        查看系统状态
  help          显示帮助信息

示例:
  ./scripts/dev-web.sh setup          # 首次设置
  ./scripts/dev-web.sh dev            # 启动开发服务器
  ./scripts/dev-web.sh check          # 代码检查
  ./scripts/dev-web.sh test           # 运行测试
  ./scripts/dev-web.sh test watch     # 测试监听模式
  ./scripts/dev-web.sh build          # 构建测试
  ./scripts/dev-web.sh deploy         # 部署到 Docker
  ./scripts/dev-web.sh full           # 完整发布流程
  ./scripts/dev-web.sh logs web       # 查看前端日志
  ./scripts/dev-web.sh status         # 查看状态

文档:
  - 完整开发指南: docs/yuri-config/customize-frontend/SAFE_LOCAL_DEV.md
  - 快速参考: docs/yuri-config/customize-frontend/QUICK_REFERENCE.md
EOF
}

# 主函数
main() {
    case "${1:-help}" in
        setup)
            setup
            ;;
        dev)
            dev
            ;;
        check)
            check
            ;;
        test)
            test "${2:-}"
            ;;
        build)
            build
            ;;
        deploy)
            deploy
            ;;
        full)
            full
            ;;
        logs)
            logs "${2:-}"
            ;;
        clean)
            clean
            ;;
        status)
            status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

