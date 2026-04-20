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
          <li><strong>仪表盘</strong>：查看追踪ETF的份额/市值趋势图，支持按标签筛选、切换时间范围（1月/3月/6月/1年/全部）</li>
          <li><strong>数据表格</strong>：支持按市值、份额、份额变化排序，支持搜索代码或名称</li>
          <li><strong>ETF管理</strong>：输入6位代码添加追踪，系统自动识别标签，可自定义标签</li>
          <li><strong>ETF详情</strong>：点击代码或名称查看单只ETF历史趋势和数据</li>
          <li><strong>手动采集</strong>：右上角按钮强制更新数据</li>
        </ul>
      </a-typography-paragraph>

      <a-typography-title :level="5">标签说明</a-typography-title>
      <a-typography-paragraph>
        <ul>
          <li><strong>系统标签（橙色）</strong>：自动从ETF名称识别，如沪深300、半导体、化工等</li>
          <li><strong>自定义标签（蓝色）</strong>：自由添加，如"核心持仓"、"定投"</li>
          <li>仪表盘筛选下拉框中可按标签快速筛选</li>
        </ul>
      </a-typography-paragraph>

      <a-typography-title :level="5">数据更新</a-typography-title>
      <a-typography-paragraph>
        <ul>
          <li>首次启动自动恢复约1年历史数据（1400+只ETF）</li>
          <li>打开页面自动补上缺失天数（每6小时最多一次）</li>
          <li>手动采集不受此限制</li>
          <li>数据来源：上交所/深交所官方 + 腾讯财经</li>
        </ul>
      </a-typography-paragraph>

      <a-typography-title :level="5">版本更新</a-typography-title>
      <a-typography-paragraph>
        <ul>
          <li>程序自动检查新版本，页面顶部会显示更新提示</li>
          <li>点击"立即更新"即可完成，更新后自动刷新页面</li>
          <li>更新不会影响你的追踪列表和自定义标签</li>
        </ul>
      </a-typography-paragraph>

      <a-typography-title :level="5">常见问题</a-typography-title>
      <a-typography-paragraph>
        <ul>
          <li><strong>端口被占用</strong>：上次未正常关闭，重启电脑即可</li>
          <li><strong>Windows 提示"已保护你的电脑"</strong>：点击"更多信息"→"仍要运行"</li>
          <li><strong>Mac 提示无法打开</strong>：终端执行 <a-typography-text code>xattr -cr ETFRadar/</a-typography-text></li>
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
