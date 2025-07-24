'use server';

import { graphqlClient } from '../api/graphql';

// Server-side GraphQL functions
export async function executeQuery<T>(
	query: string,
	variables?: Record<string, unknown>
): Promise<T> {
	const result = await graphqlClient.request(query, variables);
	return result as T;
}

export async function executeMutation<T = unknown>(
	mutation: string,
	variables?: Record<string, unknown>
): Promise<T> {
	const result = await graphqlClient.request(mutation, variables);
	return result as T;
}
