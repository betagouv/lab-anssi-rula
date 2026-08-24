export async function json<T>(reponse: Response): Promise<T> {
  if (!reponse.ok) {
    const corps = await reponse.json().catch(() => ({}));
    throw new Error(
      (corps as { detail?: string }).detail ?? `HTTP ${reponse.status}`
    );
  }
  return reponse.json() as Promise<T>;
}
