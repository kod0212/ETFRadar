<template>
  <a-modal v-model:open="visible" title="📡 ETF雷达 使用说明" width="680px" :footer="null">
    <a-typography>
      <a-typography-title :level="5">启动与关闭</a-typography-title>
      <a-typography-paragraph>
        <ul>
          <li><strong>Windows</strong>：双击 ETFRadar.exe 启动，关闭黑色命令行窗口退出</li>
          <li><strong>Mac</strong>：终端执行 ./ETFRadar 启动，Ctrl+C 退出</li>
          <li>启动后浏览器自动打开，如未打开请手动访问 <a-typography-text code>http://localhost:9528</a-typography-text></li>
          <li>关闭浏览器不会停止程序，需关闭命令行窗口</li>
        </ul>
      </a-typography-paragraph>

      <a-typography-title :level="5">功能介绍</a-typography-title>
      <a-typography-paragraph>
        <ul>
          <li><strong>仪表盘</strong>：查看追踪ETF的份额/市值趋势图，支持切换分组和指标</li>
          <li><strong>ETF管理</strong>：输入6位代码添加追踪，预置1400+只ETF历史数据，添加即可查看</li>
          <li><strong>ETF详情</strong>：点击代码查看单只ETF历史趋势和数据表格</li>
          <li><strong>手动采集</strong>：右上角按钮强制更新数据</li>
        </ul>
      </a-typography-paragraph>

      <a-typography-title :level="5">数据更新</a-typography-title>
      <a-typography-paragraph>
        <ul>
          <li>首次启动自动恢复约1年历史数据</li>
          <li>打开页面自动补上缺失天数（每6小时最多一次）</li>
          <li>手动采集不受此限制</li>
          <li>数据来源：上交所/深交所官方 + 腾讯财经</li>
        </ul>
      </a-typography-paragraph>

      <a-typography-title :level="5">常见问题</a-typography-title>
      <a-typography-paragraph>
        <ul>
          <li><strong>端口被占用</strong>：上次未正常关闭，重启电脑即可</li>
          <li><strong>Windows 提示"已保护你的电脑"</strong>：点击"更多信息"→"仍要运行"</li>
          <li><strong>Mac 提示无法打开</strong>：终端执行 <a-typography-text code>xattr -cr ETFRadar-Mac/</a-typography-text></li>
          <li><strong>遇到问题</strong>：将 log/ 文件夹发送给开发者排查</li>
        </ul>
      </a-typography-paragraph>
    </a-typography>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const visible = ref(false)
const show = () => { visible.value = true }

defineExpose({ show })
</script>
