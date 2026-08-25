<?php
header('Content-Type: application/json; charset=UTF-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Honeypot anti-spam
if (!empty($_POST['_honey'])) {
    echo json_encode(['ok' => true]);
    exit;
}

$nome     = trim(strip_tags($_POST['nome']     ?? ''));
$email    = trim(strip_tags($_POST['email']    ?? ''));
$empresa  = trim(strip_tags($_POST['empresa']  ?? ''));
$segmento = trim(strip_tags($_POST['segmento'] ?? ''));
$mensagem = trim(strip_tags($_POST['mensagem'] ?? ''));

if (!$nome || !$email || !$empresa || !$mensagem || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(422);
    echo json_encode(['error' => 'Campos inválidos']);
    exit;
}

$para    = 'contato@athostecnologia.com.br';
$assunto = '=?UTF-8?B?' . base64_encode("Novo contato — $empresa") . '?=';
$corpo   = implode("\n", [
    "Nome:      $nome",
    "E-mail:    $email",
    "Empresa:   $empresa",
    "Segmento:  $segmento",
    "",
    "Mensagem:",
    $mensagem,
]);

$headers = implode("\r\n", [
    "From: Site Athos <noreply@athostecnologia.com.br>",
    "Reply-To: $email",
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: 8bit",
    "MIME-Version: 1.0",
]);

if (mail($para, $assunto, $corpo, $headers)) {
    echo json_encode(['ok' => true]);
} else {
    http_response_code(500);
    echo json_encode(['error' => 'Falha ao enviar e-mail']);
}
