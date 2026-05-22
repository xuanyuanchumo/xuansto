<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <el-aside width="220px">
          <Suspense>
            <template #default>
              <Navigation />
            </template>
            <template #fallback>
              <div class="nav-loading">加载中...</div>
            </template>
          </Suspense>
        </el-aside>
        <el-main>
          <router-view v-slot="{ Component }">
            <Suspense>
              <template #default>
                <component :is="Component" />
              </template>
              <template #fallback>
                <div class="page-loading">
                  <el-icon class="is-loading"><Loading /></el-icon>
                  <span>页面加载中...</span>
                </div>
              </template>
            </Suspense>
          </router-view>
        </el-main>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { defineAsyncComponent } from 'vue'
import { ElConfigProvider } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const Navigation = defineAsyncComponent(() => 
  import('@/components/Navigation.vue')
)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.app-container {
  height: 100%;
}

.el-container {
  height: 100%;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}

.nav-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #fff;
  font-size: 14px;
}

.page-loading {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 400px;
  gap: 10px;
  color: #409eff;
  font-size: 16px;
}

.page-loading .el-icon {
  font-size: 32px;
}
</style>
