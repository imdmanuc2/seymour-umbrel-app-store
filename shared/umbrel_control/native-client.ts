import fs from 'node:fs/promises'
import process from 'node:process'
import * as jwt from '/opt/umbreld/source/modules/jwt.ts'

type Args = {
	dataDirectory: string
	endpoint: string
	action: string
	appId?: string
}

function parseArgs(argv: string[]): Args {
	let dataDirectory = '/home/umbrel/umbrel'
	let endpoint = 'http://localhost/trpc'
	const positional: string[] = []

	for (let index = 0; index < argv.length; index += 1) {
		const value = argv[index]

		if (value === '--data-directory') {
			dataDirectory = argv[index + 1]
			index += 1
			continue
		}

		if (value === '--endpoint') {
			endpoint = argv[index + 1]
			index += 1
			continue
		}

		positional.push(value)
	}

	if (!positional[0]) {
		throw new Error('Missing action')
	}

	return {
		dataDirectory,
		endpoint,
		action: positional[0],
		appId: positional[1],
	}
}

async function token(dataDirectory: string): Promise<string> {
	const secret = await fs.readFile(
		`${dataDirectory}/secrets/jwt`,
		'utf8',
	)
	return jwt.sign(secret)
}

function procedure(action: string): {
	path: string
	method: 'GET' | 'POST'
	input: unknown
} {
	switch (action) {
		case 'list':
			return {path: 'apps.list', method: 'GET', input: undefined}
		case 'state':
			return {path: 'apps.state', method: 'GET', input: null}
		case 'logs':
			return {path: 'apps.logs', method: 'GET', input: null}
		case 'install':
			return {path: 'apps.install', method: 'POST', input: null}
		case 'uninstall':
			return {path: 'apps.uninstall', method: 'POST', input: null}
		case 'restart':
			return {path: 'apps.restart', method: 'POST', input: null}
		case 'start':
			return {path: 'apps.start', method: 'POST', input: null}
		case 'stop':
			return {path: 'apps.stop', method: 'POST', input: null}
		case 'update':
			return {path: 'apps.update', method: 'POST', input: null}
		default:
			throw new Error(`Unsupported action: ${action}`)
	}
}

async function call(args: Args): Promise<unknown> {
	const spec = procedure(args.action)

	if (args.action !== 'list' && !args.appId) {
		throw new Error(`${args.action} requires appId`)
	}

	const input =
		args.action === 'list'
			? undefined
			: {appId: args.appId}

	const authToken = await token(args.dataDirectory)
	const base = `${args.endpoint}/${spec.path}`

	const headers: Record<string, string> = {
		Authorization: `Bearer ${authToken}`,
		'Content-Type': 'application/json',
	}

	let response: Response

	if (spec.method === 'GET') {
		const url =
			input === undefined
				? base
				: `${base}?input=${encodeURIComponent(
						JSON.stringify({json: input}),
					)}`
		response = await fetch(url, {headers})
	} else {
		response = await fetch(base, {
			method: 'POST',
			headers,
			body: JSON.stringify({json: input}),
		})
	}

	const text = await response.text()
	let payload: unknown

	try {
		payload = JSON.parse(text)
	} catch {
		payload = {raw: text}
	}

	if (!response.ok) {
		throw new Error(
			`Umbrel TRPC ${spec.path} failed: ${response.status} ${text}`,
		)
	}

	return payload
}

const args = parseArgs(process.argv.slice(2))
const result = await call(args)
process.stdout.write(JSON.stringify(result, null, 2) + '\n')
