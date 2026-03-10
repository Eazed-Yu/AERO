<template>
  <div class="qa-view">
    <iframe
      src="http://localhost:8030"
      class="lightrag-iframe"
      frameborder="0"
    />
  </div>
</template>

<script setup lang="ts">
// LightRAG Web UI 通过 iframe 嵌入
</script>

<style scoped>
.qa-view {
  height: calc(100vh - 48px);
  padding: 0;
}

.lightrag-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
