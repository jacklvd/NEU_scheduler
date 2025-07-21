import { GraphQLClient } from 'graphql-request';

const GRAPHQL_ENDPOINT =
	process.env.NEXT_PUBLIC_GRAPHQL_ENDPOINT ||
	'http://localhost:8000/api/graphql';

export const graphqlClient = new GraphQLClient(GRAPHQL_ENDPOINT, {
	headers: {
		'Content-Type': 'application/json',
	},
});

// GraphQL queries
export const GET_TERMS = `
  query GetTerms($maxResults: Int = 20) {
    getTerms(maxResults: $maxResults) {
      id
      name
    }
  }
`;

export const GET_SUBJECTS = `
  query GetSubjects($term: String!, $searchTerm: String = "") {
    getSubjects(term: $term, searchTerm: $searchTerm) {
      code
      name
    }
  }
`;

export const SEARCH_COURSES = `
  query SearchCourses($term: String!, $subject: String = "", $courseNumber: String = "", $pageSize: Int = 20) {
    searchCourses(term: $term, subject: $subject, courseNumber: $courseNumber, pageSize: $pageSize) {
      crn
      title
      subject
      courseNumber
      instructor
      meetingDays
      meetingTimes
      location
      enrollment
      enrollmentCap
      credits
    }
  }
`;

export const SUGGEST_PLAN = `
  query SuggestPlan($interest: String!, $years: Int = 2) {
    suggestPlan(interest: $interest, years: $years) {
      year
      term
      courses
    }
  }
`;

export const SAVE_SCHEDULE = `
  mutation SaveSchedule($userId: String!, $year: Int!, $term: String!, $courses: [String!]!) {
    saveSchedule(userId: $userId, year: $year, term: $term, courses: $courses)
  }
`;
