from api import CourseNaviInterface


class TaskManager:
    def __init__(self, all=False, verbose=False, debug=False):
        pass

    def pull(self):
        """Pull files from CourseNavi."""
        cni = CourseNaviInterface()

        dashboard = cni.login()
        courses = cni.get_courses(dashboard)

        for title, course in courses:
            print(f'> Course title: {title}')

            course_detail = cni.select_course(course, dashboard)
            lectures = cni.get_lectures(course_detail)

            print(f' > Found {len(lectures)} lectures')

            for title, lecture in lectures:
                print(f'  > {title}')

                # files = cni.get_lecture_files(lecture)


