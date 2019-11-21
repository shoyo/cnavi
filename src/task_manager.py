from api import (CourseNaviInterface,
                 InvalidCredentialsError,
                 NoCredentialsError)


class TaskManager:
    def __init__(self, all=False, verbose=False, debug=False):
        self.api = CourseNaviInterface()

    def pull(self):
        """Pull files from CourseNavi."""
        try:
            dashboard = self.api.login()
        except NoCredentialsError:
            print("[No credentials] Please set your CourseNavi email and "
                  + "password with `cnavi config`")
            return
        except InvalidCredentialsError:
            print("[Login error] There was an issue logging in. If you think "
                  + "this is an application error, please let me know at "
                  + "shoyoinokuchi@gmail.com. Otherwise, your can reset your "
                  + "credentials with `cnavi config`.")
            return

        courses = self.api.get_courses(dashboard)

        for title, course in courses:
            print(f'> Course title: {title}')

            course_detail = self.api.select_course(course, dashboard)
            lectures = self.api.get_lectures(course_detail)

            print(f' > Found {len(lectures)} lectures')

            for title, lecture in lectures:
                print(f'  > {title}')

                lecture_detail = self.api.select_lecture(lecture,
                                                         course_detail)
#                print(lecture_detail.prettify())

                break
            break

