from api import CourseNaviInterface


class TaskManager:
    def __init__(self):
        self.api = CourseNaviInterface()

    def pull(self, all=False, verbose=False, debug=False):
        """Pull files from CourseNavi."""
        dashboard = self.api.login()
        courses = self.api.get_courses(dashboard)

        for title, course in courses:
            print(f'> Course title: {title}')

            course_detail = self.api.select_course(course, dashboard)
            lectures = self.api.get_lectures(course_detail)

            print(f' > Found {len(lectures)} lectures')

            for title, lecture in lectures:
                print(f'  > {title}')

                # files = self.api.get_lecture_files(lecture)


