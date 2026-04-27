import apiFetch from './auth';

export const teamsApi = {
  getTeams: () => apiFetch('/api/teams/'),
  
  getTeam: (id) => apiFetch(`/api/teams/${id}/`),
  
  createTeam: (teamData) => apiFetch('/api/teams/', {
    method: 'POST',
    body: JSON.stringify(teamData)
  }),
  
  updateTeam: (id, teamData) => apiFetch(`/api/teams/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(teamData)
  }),
  
  deleteTeam: (id) => apiFetch(`/api/teams/${id}/`, {
    method: 'DELETE'
  }),
  
  addMember: (teamId, username) => apiFetch(`/api/teams/${teamId}/members/`, {
    method: 'POST',
    body: JSON.stringify({ username })
  }),
  
  removeMember: (teamId, userId) => apiFetch(`/api/teams/${teamId}/members/${userId}/`, {
    method: 'DELETE'
  }),
  
  getTeamMembers: (teamId) => apiFetch(`/api/teams/${teamId}/team-members/`),
  
  getUserTeams: () => apiFetch('/api/user-teams/')
};
