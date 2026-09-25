<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ChessBoard from './components/ChessBoard.vue'

const systemOneConfig = ref({
  baseUrl: '/api',
  model: 'von-latest'
})

const availableModels = ref<string[]>([]);

async function getModels(): Promise<string[]> {
    const url = `${systemOneConfig.value.baseUrl}/v1/models`;
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Accept': 'application/json'
        }
    })
    const responseBody = (await response.json());
    return responseBody.models.map((x: any) => x.name)
}

onMounted(async () => {
  const models = await getModels();
  availableModels.value = models
})

</script>

<template>
  <section style="width: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 4px;">
    <fieldset>
      <small>You can enter the base url to your <a href="https://github.com/wfzyx/von#wire-protocol-verification" target="_blank">custom system one server</a>.</small>
      <br>
      <br>
      <label>System One Server Base Url: </label>
      <input 
        type="text" 
        placeholder="http://localhost:8000" 
        v-model="systemOneConfig.baseUrl"
      />
      <br>
      <label>Model: </label>
      <select v-model="systemOneConfig.model">
        <option v-for="modelName in availableModels" :key="modelName">{{ modelName }}</option>
      </select>
    </fieldset>
    <ChessBoard 
      v-bind:system-one-server-config="systemOneConfig"
    />
  </section>
</template>
