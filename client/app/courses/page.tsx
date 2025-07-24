import { CourseSearch } from '@/components/course-search';

export default function CoursesPage() {
	return (
		<div className="container mx-auto px-4 py-8">
			<div className="mb-8">
				<h1 className="text-3xl font-bold mb-2 text-northeastern-black">
					Course Search
				</h1>
				<p className="text-northeastern-gray">
					Search and browse courses available at Northeastern University
				</p>
			</div>
			<CourseSearch />
		</div>
	);
}
