export function notificationApresAnalyse(
  ongletActif: 'analyse' | 'transcript',
  statut: 'prete' | 'echec'
): 'prete' | 'echec' | '' {
  return ongletActif === 'transcript' ? statut : '';
}
