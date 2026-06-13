import { http } from './http'

export const memberApi = {
  list: () => http.get('/members'),
  create: (payload) => http.post('/members', payload),
  update: (id, payload) => http.patch(`/members/${id}`, payload),
  getDuplicates: () => http.get('/members/duplicates'),
  merge: (source_member_id, target_member_id) =>
    http.post('/members/merge', { source_member_id, target_member_id }),
}
