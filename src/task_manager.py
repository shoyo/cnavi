from api import CourseNaviInterface


class TaskManager:
    def __init__(self):
        pass

    def pull(self):
        """Pull files from CourseNavi."""
        cni = CourseNaviInterface()

        dashboard = cni.login()
        courses = cni.get_courses(dashboard)

        for course in courses:
            title = cni.get_title(course)
            print(f'> Course title: {title}')
            lectures = cni.select_course(course, dashboard)
            break
#            for lecture in lectures:
#                file = cni.get_file(lecture)



        

