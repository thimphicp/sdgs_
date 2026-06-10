param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8090,
    [string]$Provider = "groovellm",
    [string]$ApiKey = ""
)

$ErrorActionPreference = "Stop"

if ($ApiKey) {
    $env:LOCAL_LLM_API_KEY = $ApiKey
}

$env:LOCAL_LLM_API_HOST = $Host
$env:LOCAL_LLM_API_PORT = "$Port"
$env:LOCAL_LLM_PROVIDER = $Provider

python -m sdgs.local_llm_api.server
