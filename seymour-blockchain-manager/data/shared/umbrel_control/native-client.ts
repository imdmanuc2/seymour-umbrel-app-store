import process from 'node:process'


type ParsedArguments = {
	dataDirectory: string
	endpoint: string
	action: string
	appId?: string
}


function parseArguments(
	argv: string[],
): ParsedArguments {
	let dataDirectory = '/home/umbrel/umbrel'
	let endpoint = 'ws://localhost/trpc'
	const positional: string[] = []

	for (
		let index = 0;
		index < argv.length;
		index += 1
	) {
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


function queryForAction(
	action: string,
): string {
	const queries: Record<string, string> = {
		list: 'apps.list.query',
		state: 'apps.state.query',
		logs: 'apps.logs.query',
		install: 'apps.install.mutate',
		uninstall: 'apps.uninstall.mutate',
		restart: 'apps.restart.mutate',
		start: 'apps.start.mutate',
		stop: 'apps.stop.mutate',
		update: 'apps.update.mutate',
	}

	const query = queries[action]

	if (!query) {
		throw new Error(
			`Unsupported action: ${action}`,
		)
	}

	return query
}


async function main(): Promise<void> {
	const parsed = parseArguments(
		process.argv.slice(2),
	)

	process.env.UMBREL_DATA_DIR =
		parsed.dataDirectory

	process.env.UMBREL_TRPC_ENDPOINT =
		parsed.endpoint

	const {cliClient} = await import(
		'/opt/umbreld/source/modules/cli-client.ts'
	)

	if (
		parsed.action !== 'list'
		&& !parsed.appId
	) {
		throw new Error(
			`${parsed.action} requires appId`,
		)
	}

	const args =
		parsed.action === 'list'
			? []
			: [
					'--appId',
					parsed.appId!,
				]

	await cliClient({
		query: queryForAction(
			parsed.action,
		),
		args,
	})

	await new Promise<void>((resolve) => {
		setTimeout(resolve, 500)
	})

	process.exit(0)
}


main().catch((error) => {
	const message =
		error instanceof Error
			? error.message
			: String(error)

	process.stderr.write(
		message + '\n',
	)

	process.exit(1)
})
