# Platina de Shadow of the Tomb Raider — acompanhamento Steam

Conta Steam: `76561199102269125`. Jogo: `750920`.

Este repositório consulta suas conquistas aproximadamente a cada 6 horas com GitHub Actions e, quando funciona, publica `achievements.json`. O agendamento pode atrasar e **não é acompanhamento instantâneo**.

O arquivo público revela nomes das conquistas **desbloqueadas** e apenas identificadores técnicos das pendentes, evitando spoilers desnecessários.

## Testar a sincronização

1. Abra **Actions → Sincronizar conquistas da Steam → Run workflow** e inicie uma execução na branch `main`.
2. Confira se a execução ficou verde e se o arquivo `achievements.json` apareceu na raiz do repositório.
3. Se a execução falhar com `STEAM_API_KEY is not configured`, a fonte XML pública não estava disponível. Caso sua conta tenha acesso, gere uma chave no site https://steamcommunity.com/dev/apikey e adicione-a em **Settings → Secrets and variables → Actions → New repository secret**, com nome `STEAM_API_KEY`. Rode o workflow novamente.
4. Se houver falha de permissão ao gravar, confira **Settings → Actions → General → Workflow permissions**. Quando disponível, habilite **Read and write permissions**.
5. Nunca cole a chave em um arquivo ou nesta conversa.

Depois, diga ao ChatGPT: **"Atualize minha platina lendo o achievements.json do repositório LucasMR121/-steam-platina"**.

O projeto consulta somente dados que a Steam disponibiliza publicamente ou por API autorizada. Não contorna privacidade nem restrições de acesso. 
