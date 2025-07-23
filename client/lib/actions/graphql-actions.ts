'use server';

import { graphqlClient } from '../api/graphql';

// Server-side GraphQL functions
export async function executeQuery<T>(
	query: string,
	variables?: Record<string, unknown>
): Promise<T> {
	return await graphqlClient.request<T>(query, variables);
}

export async function executeMutation<T = unknown>(
	mutation: string,
	variables?: Record<string, unknown>
): Promise<T> {
	return await graphqlClient.request<T>(mutation, variables);
}
