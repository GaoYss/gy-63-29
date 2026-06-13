<template>
  <div class="page-stack">
    <section class="stats-grid">
      <StatCard label="会员总数" :value="members.length" hint="当前系统会员" :icon="Users" />
      <StatCard label="总积分" :value="totalPoints" hint="可兑换权益池" :icon="BadgePercent" />
      <StatCard label="最高等级" :value="topLevelName" hint="按积分门槛" :icon="Crown" />
      <StatCard label="偏好分类" :value="favoriteCount" hint="推荐依据" :icon="Tags" />
    </section>

    <section class="toolbar-panel">
      <label>
        会员搜索
        <input v-model="keyword" placeholder="输入姓名、手机号或偏好" />
      </label>
      <label>
        等级筛选
        <select v-model.number="levelFilter">
          <option :value="0">全部等级</option>
          <option v-for="level in levels" :key="level.id" :value="level.id">{{ level.name }}</option>
        </select>
      </label>
      <button class="secondary-button" @click="checkDuplicates">
        <UsersMerge class="icon-inline" />
        检查重复手机号
      </button>
    </section>

  <div v-if="duplicates.length" class="panel merge-panel">
    <div class="panel-header">
      <h2><UsersMerge class="icon-inline" /> 重复手机号会员</h2>
      <span class="count-badge warn">{{ duplicates.length }} 个手机号重复</span>
    </div>
    <div v-for="group in duplicates" :key="group.phone" class="duplicate-group">
      <div class="duplicate-phone">
        <strong>{{ group.phone }}</strong>
        <span>共 {{ group.members.length }} 个账号</span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>姓名</th>
            <th>等级</th>
            <th>积分</th>
            <th>偏好</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="member in group.members"
            :key="member.id"
            :class="{
              'merge-source': selectedSource?.id === member.id,
              'merge-target': selectedTarget?.id === member.id,
            }"
          >
            <td>{{ member.name }}</td>
            <td>{{ member.level?.name }}</td>
            <td>{{ member.points }}</td>
            <td>{{ member.favorite_categories.join('、') }}</td>
            <td>
              <div class="action-buttons">
                <button
                  class="small-button"
                  :class="{ active: selectedSource?.id === member.id }"
                  @click.stop="selectSource(member)"
                >
                  设为源
                </button>
                <button
                  class="small-button primary"
                  :class="{ active: selectedTarget?.id === member.id }"
                  @click.stop="selectTarget(member)"
                >
                  设为目标
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="selectedSource && selectedTarget && selectedSource.phone === selectedTarget.phone" class="merge-actions">
        <div class="merge-preview">
          <span>将 <strong>{{ selectedSource.name }}</strong> (ID: {{ selectedSource.id }}) 的积分和记录合并到</span>
          <span> <strong>{{ selectedTarget.name }}</strong> (ID: {{ selectedTarget.id }})</span>
        </div>
        <button class="primary-button" @click="doMerge">
          确认合并
        </button>
        <button class="secondary-button" @click="clearMergeSelection">
          取消
        </button>
      </div>
    </div>
  </div>

  <div class="content-grid two-columns">
    <section class="panel">
      <div class="panel-header">
        <h2>会员列表</h2>
        <span class="count-badge">{{ filteredMembers.length }} 人</span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>姓名</th>
            <th>手机号</th>
            <th>等级</th>
            <th>积分</th>
            <th>偏好</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="member in filteredMembers"
            :key="member.id"
            :class="{ selected: selectedMember?.id === member.id }"
            @click="selectMember(member)"
          >
            <td>{{ member.name }}</td>
            <td>{{ member.phone }}</td>
            <td>{{ member.level?.name }}</td>
            <td>{{ member.points }}</td>
            <td>{{ member.favorite_categories.join('、') }}</td>
          </tr>
        </tbody>
      </table>
      <EmptyState v-if="!filteredMembers.length" text="暂无匹配会员" />
    </section>

    <section class="panel">
      <div class="panel-header">
        <h2>{{ selectedMember ? '会员详情' : '新增会员' }}</h2>
      </div>
      <div v-if="selectedMember" class="detail-box">
        <strong>{{ selectedMember.name }}</strong>
        <span>{{ selectedMember.phone }} · {{ selectedMember.level?.name }}</span>
        <p>当前积分 {{ selectedMember.points }}，偏好 {{ selectedMember.favorite_categories.join('、') || '暂无' }}</p>
        <button class="secondary-button" @click="selectedMember = null">切换为新增</button>
      </div>
      <MessageBanner :message="message" :type="messageType" />
      <form class="form-stack" @submit.prevent="submit">
        <label>
          姓名
          <input v-model="form.name" required placeholder="请输入姓名" />
        </label>
        <label>
          手机号
          <input v-model="form.phone" required placeholder="请输入手机号" />
        </label>
        <label>
          会员等级
          <select v-model.number="form.level_id">
            <option v-for="level in levels" :key="level.id" :value="level.id">
              {{ level.name }}
            </option>
          </select>
        </label>
        <label>
          初始积分
          <input v-model.number="form.points" min="0" type="number" />
        </label>
        <label>
          偏好分类
          <input v-model="favoriteText" placeholder="用逗号分隔，如 柑橘,莓果" />
        </label>
        <button class="primary-button" type="submit">保存会员</button>
      </form>
    </section>
  </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { BadgePercent, Crown, Tags, Users, UsersMerge } from 'lucide-vue-next'

import { levelApi } from '../api/levels'
import { memberApi } from '../api/members'
import { fallbackLevels, fallbackMembers } from '../api/fallback'
import EmptyState from '../components/EmptyState.vue'
import MessageBanner from '../components/MessageBanner.vue'
import StatCard from '../components/StatCard.vue'
import { keepList } from '../utils/dataState'

const members = ref([...fallbackMembers])
const levels = ref([...fallbackLevels])
const duplicates = ref([])
const favoriteText = ref('')
const message = ref('')
const messageType = ref('success')
const keyword = ref('')
const levelFilter = ref(0)
const selectedMember = ref(null)
const selectedSource = ref(null)
const selectedTarget = ref(null)
const form = reactive({
  name: '',
  phone: '',
  level_id: 1,
  points: 0,
})

const filteredMembers = computed(() => {
  const text = keyword.value.trim().toLowerCase()
  return members.value.filter((member) => {
    const matchesText =
      !text ||
      [member.name, member.phone, member.level?.name, ...member.favorite_categories]
        .join(' ')
        .toLowerCase()
        .includes(text)
    const matchesLevel = !levelFilter.value || member.level_id === levelFilter.value
    return matchesText && matchesLevel
  })
})

const totalPoints = computed(() => members.value.reduce((sum, member) => sum + member.points, 0))
const topLevelName = computed(() => levels.value.at(-1)?.name || '-')
const favoriteCount = computed(() => new Set(members.value.flatMap((member) => member.favorite_categories)).size)

async function loadData() {
  const [memberList, levelList] = await Promise.all([
    memberApi.list().catch(() => fallbackMembers),
    levelApi.list().catch(() => fallbackLevels),
  ])
  members.value = keepList(memberList, members.value)
  levels.value = keepList(levelList, levels.value)
  form.level_id = levelList[0]?.id || 1
}

async function submit() {
  try {
    await memberApi.create({
      ...form,
      favorite_categories: favoriteText.value
        .split(/[,，]/)
        .map((item) => item.trim())
        .filter(Boolean),
    })
    Object.assign(form, { name: '', phone: '', points: 0, level_id: levels.value[0]?.id || 1 })
    favoriteText.value = ''
    message.value = '会员已保存'
    messageType.value = 'success'
    await loadData()
  } catch (error) {
    message.value = error.message
    messageType.value = 'error'
  }
}

function selectMember(member) {
  selectedMember.value = member
}

async function checkDuplicates() {
  try {
    const data = await memberApi.getDuplicates().catch(() => [])
    duplicates.value = data
    if (data.length === 0) {
      message.value = '未发现重复手机号的会员'
      messageType.value = 'success'
    } else {
      message.value = `发现 ${data.length} 个重复手机号`
      messageType.value = 'warn'
    }
  } catch (error) {
    message.value = error.message
    messageType.value = 'error'
  }
}

function selectSource(member) {
  if (selectedTarget?.id === member.id) {
    selectedTarget.value = null
  }
  selectedSource.value = member
}

function selectTarget(member) {
  if (selectedSource?.id === member.id) {
    selectedSource.value = null
  }
  selectedTarget.value = member
}

function clearMergeSelection() {
  selectedSource.value = null
  selectedTarget.value = null
}

async function doMerge() {
  if (!selectedSource.value || !selectedTarget.value) {
    return
  }
  try {
    const result = await memberApi.merge(selectedSource.value.id, selectedTarget.value.id)
    message.value = `合并成功！合并积分 ${result.merged_points}，${result.merged_records_count} 条积分记录，${result.merged_orders_count} 条预售订单`
    messageType.value = 'success'
    clearMergeSelection()
    await Promise.all([loadData(), checkDuplicates()])
  } catch (error) {
    message.value = error.message
    messageType.value = 'error'
  }
}

onMounted(loadData)
</script>
