from api import CourseNaviInterface


class TaskManager:
    def __init__(self):
        pass

    def pull(self):
        """Pull files from CourseNavi."""
        cni = CourseNaviInterface()

        dashboard = cni.login()
        courses = cni.get_courses(dashboard)
        print(courses)

#        for course in courses:
#            lectures = cni.get_lectures(course)
#            for lecture in lectures:
#                file = cni.get_file(lecture)



        

