<template>
  <div class="navigation">
    <div class="logo">
      <h3>三省六部</h3>
    </div>
    
    <el-menu
      :default-active="activeMenu"
      class="nav-menu"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
      router
    >
      <el-menu-item index="/">
        <el-icon><DataBoard /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      
      <el-menu-item index="/projects">
        <el-icon><Folder /></el-icon>
        <span>项目列表</span>
      </el-menu-item>
      
      <el-menu-item index="/projects/create">
        <el-icon><FolderAdd /></el-icon>
        <span>创建项目</span>
      </el-menu-item>
      
      <el-menu-item index="/tasks">
        <el-icon><List /></el-icon>
        <span>任务管理</span>
      </el-menu-item>
      
      <el-menu-item index="/statistics">
        <el-icon><TrendCharts /></el-icon>
        <span>系统统计</span>
      </el-menu-item>
      
      <el-menu-item index="/skill-calls">
        <el-icon><Document /></el-icon>
        <span>技能调用</span>
      </el-menu-item>
      
      <el-menu-item index="/agents">
        <el-icon><User /></el-icon>
        <span>Agent 管理</span>
      </el-menu-item>
      
      <el-sub-menu index="evolution-monitor">
        <template #title>
          <el-icon><Monitor /></el-icon>
          <span>演化监控</span>
        </template>
        <el-menu-item index="/skill-health">
          <el-icon><FirstAidKit /></el-icon>
          <span>技能健康度</span>
        </el-menu-item>
        <el-menu-item index="/path-validation">
          <el-icon><FolderChecked /></el-icon>
          <span>路径验证</span>
        </el-menu-item>
        <el-menu-item index="/evolution-knowledge">
          <el-icon><Share /></el-icon>
          <span>演化知识库</span>
        </el-menu-item>
        <el-menu-item index="/realtime-evolution">
          <el-icon><DataLine /></el-icon>
          <span>实时演化状态</span>
        </el-menu-item>
      </el-sub-menu>
      
      <el-sub-menu index="departments">
        <template #title>
          <el-icon><OfficeBuilding /></el-icon>
          <span>三省六部</span>
        </template>
        
        <el-sub-menu index="zhongshusheng">
          <template #title>中书省</template>
          <el-menu-item index="/dept/zhongshusheng">决策中心</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="menxiasheng">
          <template #title>门下省</template>
          <el-menu-item index="/dept/menxiasheng">审议中心</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu index="shangshusheng">
          <template #title>尚书省</template>
          <el-menu-item index="/dept/libu">吏部</el-menu-item>
          <el-menu-item index="/dept/hubu">户部</el-menu-item>
          <el-menu-item index="/dept/liibu">礼部</el-menu-item>
          <el-menu-item index="/dept/bingbu">兵部</el-menu-item>
          <el-menu-item index="/dept/xingbu">刑部</el-menu-item>
          <el-menu-item index="/dept/gongbu">工部</el-menu-item>
        </el-sub-menu>
      </el-sub-menu>
    </el-menu>
    
    <div class="notification-area">
      <NotificationCenter />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { DataBoard, Document, User, OfficeBuilding, FolderAdd, List, Folder, TrendCharts, Monitor, FirstAidKit, FolderChecked, Share, DataLine } from '@element-plus/icons-vue'
import NotificationCenter from './NotificationCenter.vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped>
.navigation {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
  color: #fff;
}

.logo h3 {
  margin: 0;
  font-size: 18px;
}

.nav-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}

.nav-menu:not(.el-menu--collapse) {
  width: 220px;
}

.notification-area {
  padding: 10px;
  background-color: #263445;
  border-top: 1px solid #3a4a5d;
}
</style>
