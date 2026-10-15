import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { describeKeySource, systemOne, TypeSafeError } from '../dist/client.js';

const savedEnv = {
  TYPESAFE_API_KEY: process.env.TYPESAFE_API_KEY,
  JEV_API_KEY: process.env.JEV_API_KEY,
  TYPESAFE_KEY_FILE: process.env.TYPESAFE_KEY_FILE,
};

function restoreEnv() {
  for (const [key, value] of Object.entries(savedEnv)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
}

function hideKeys() {
  delete process.env.TYPESAFE_API_KEY;
  delete process.env.JEV_API_KEY;
  process.env.TYPESAFE_KEY_FILE = path.join(tmpdir(), 'jev-no-such-key-file');
}

function jsonResponse(status, body, headers = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });
}

test('systemOne redacts secrets in the request body and never sends them', async () => {
  const bodies = [];
  const fetch = async (_url, init) => {
    bodies.push(init.body);
    return jsonResponse(200, {
      model: 'jev-1.13.0',
      answers: { ok: { type: 'noul', noul: 0.9 } },
      usage: { input_tokens: 10, output_tokens: 2 },
    });
  };

  await systemOne(
    {
      state: { note: 'here is apikey_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' },
      questions: { ok: { type: 'noul', instructions: 'ok?' } },
    },
    { apiKey: 'test-key-value', fetch },
  );

  assert.equal(bodies.length, 1);
  assert.equal(bodies[0].includes('apikey_'), false);
  assert.equal(bodies[0].includes('[REDACTED]'), true);
  assert.equal(bodies[0].includes('test-key-value'), false);
});

test('systemOne retries 429 then succeeds', async () => {
  let n = 0;
  const fetch = async () => {
    n += 1;
    if (n === 1) return jsonResponse(429, { error: 'slow down' }, { 'retry-after': '0' });
    return jsonResponse(200, { model: 'jev-1.13.0', answers: { x: { type: 'noul', noul: 1 } } });
  };
  const res = await systemOne(
    { state: 'hi', questions: { x: { type: 'noul', instructions: 'yes?' } } },
    { apiKey: 'test-key-value', fetch, retries: 2 },
  );
  assert.equal(n, 2);
  assert.equal(res.answers.x.noul, 1);
});

test('describeKeySource is none when env and files are missing', () => {
  hideKeys();
  try {
    assert.equal(describeKeySource(), 'none');
    process.env.TYPESAFE_API_KEY = '   ';
    assert.equal(describeKeySource(), 'none');
  } finally {
    restoreEnv();
  }
});

test('describeKeySource reports file or env', () => {
  hideKeys();
  const dir = mkdtempSync(path.join(tmpdir(), 'jev-key-'));
  try {
    const file = path.join(dir, 'api_key');
    writeFileSync(file, 'test-key-value\n');
    process.env.TYPESAFE_KEY_FILE = file;
    assert.equal(describeKeySource(), 'file');
    process.env.JEV_API_KEY = 'test-key-value';
    assert.equal(describeKeySource(), 'env');
  } finally {
    rmSync(dir, { recursive: true, force: true });
    restoreEnv();
  }
});

test('systemOne throws TypeSafeError without echoing the key', async () => {
  const fetch = async () => jsonResponse(401, { error: 'nope' });
  await assert.rejects(
    () =>
      systemOne(
        { state: 'hi', questions: { x: { type: 'noul', instructions: 'yes?' } } },
        { apiKey: 'super-secret-key-value', fetch },
      ),
    (err) => {
      assert.equal(err instanceof TypeSafeError, true);
      assert.equal(err.status, 401);
      assert.equal(String(err.message).includes('super-secret-key-value'), false);
      return true;
    },
  );
});
