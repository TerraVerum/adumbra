class Pagination:

    start = 0
    end = 0

    def __init__(self, length, limit, current_page=1):
        self.length = length
        self.limit = limit
        self.pages = int((length - 1) / limit) + 1
        self.current_page = current_page

        self.calculate_start_end(current_page)

    def calculate_start_end(self, current_page):

        # 1 <= current_page <= nb pages
        self.current_page = min(max(1, current_page), self.pages)

        self.start = (current_page - 1) * self.limit
        self.end = self.start + self.limit

        self.end = min(self.end, self.length)

    def export(self):
        return {
            "start": self.start,
            "end": self.end,
            "pages": self.pages,
            "page": self.current_page,
            "total": self.length,
            "showing": self.end - self.start,
        }
